import feedparser
import requests
from datetime import datetime
from difflib import SequenceMatcher
import os

KAKAO_ACCESS_TOKEN = os.environ.get("KAKAO_ACCESS_TOKEN", "")

RSS_FEEDS = {
    "유통/백화점": [
        "https://news.google.com/rss/search?q=백화점+유통&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=롯데+신세계+이마트&hl=ko&gl=KR&ceid=KR:ko",
        "https://www.hankyung.com/feed/distribution",
    ],
    "AI/테크": [
        "https://news.google.com/rss/search?q=AI+인공지능&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=반도체+엔비디아&hl=ko&gl=KR&ceid=KR:ko",
        "https://www.aitimes.com/rss/allArticle.xml",
    ],
    "주식/경제": [
        "https://news.google.com/rss/search?q=코스피+증시&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=금리+환율+경제&hl=ko&gl=KR&ceid=KR:ko",
        "https://www.mk.co.kr/rss/30300001/",
    ],
}


KEYWORDS = {
    "유통/백화점": [
        "백화점", "유통", "롯데", "신세계", "현대백화점", "이마트", "쿠팡",
        "온라인몰", "리테일", "소비", "편의점", "마트", "면세"
    ],
    "AI/테크": [
        "AI", "인공지능", "챗GPT", "LLM", "머신러닝", "딥러닝", "엔비디아",
        "테크", "IT", "디지털", "반도체", "클라우드", "데이터"
    ],
    "주식/경제": [
        "주식", "증시", "코스피", "코스닥", "금리", "환율", "경제",
        "투자", "펀드", "ETF", "채권", "기준금리", "상승", "하락",
        "시장", "지수", "달러", "원화", "GDP", "물가", "인플레",
        "Fed", "한은", "기업", "실적", "매출", "영업이익"
    ],
}

NEWS_PER_CATEGORY = 3
MAX_TITLE_LENGTH = 40


from difflib import SequenceMatcher

def is_similar(title1, title2, threshold=0.7):
    return SequenceMatcher(None, title1, title2).ratio() > threshold

def fetch_news(feeds):
    result = {}
    seen_links = set()
    seen_titles = []  # 유사도 비교용
    for category, urls in feeds.items():
        items = []
        keywords = KEYWORDS.get(category, [])
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    title = entry.get("title", "").strip()
raw_link = entry.get("link", "").strip()
# 구글 뉴스 리다이렉트 URL에서 실제 URL 추출
from urllib.parse import urlparse, parse_qs
if "news.google.com" in raw_link:
    qs = parse_qs(urlparse(raw_link).query)
    link = qs.get("url", [raw_link])[0]
else:
    link = raw_link
                    if not title or not link:
                        continue
                    if link in seen_links:
                        continue
                    if keywords and not any(kw in title for kw in keywords):
                        continue
                    # 유사 제목 중복 체크
                    if any(is_similar(title, t) for t in seen_titles):
                        continue
                    if len(title) > MAX_TITLE_LENGTH:
                        title = title[:MAX_TITLE_LENGTH] + "..."
                    items.append({"title": title, "link": link})
                    seen_links.add(link)
                    seen_titles.append(title)
                    if len(items) >= NEWS_PER_CATEGORY:
                        break
            except Exception as e:
                print(f"[오류] {category} - {url}: {e}")
                continue
            if len(items) >= NEWS_PER_CATEGORY:
                break
        result[category] = items[:NEWS_PER_CATEGORY]
    return result


def build_message(news):
    today = datetime.now().strftime("%m월 %d일 (%a)")
    weekday_map = {
        "Mon": "월", "Tue": "화", "Wed": "수",
        "Thu": "목", "Fri": "금", "Sat": "토", "Sun": "일"
    }
    for en, ko in weekday_map.items():
        today = today.replace(en, ko)

    lines = [f"[뉴스 브리핑] {today}", ""]

    for category, items in news.items():
        if not items:
            lines.append(f"▪ {category}")
            lines.append("  · 관련 뉴스 없음")
            lines.append("")
            continue
        lines.append(f"▪ {category}")
        for item in items:
            lines.append(f"  · {item['title']}")
            lines.append(f"    {item['link']}")
        lines.append("")

    lines.append("─────────────────")
    lines.append("좋은 하루 되세요!")
    return "\n".join(lines)


def send_to_kakao(message, token):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    import json
    payload = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": message,
            "link": {
                "web_url": "https://www.naver.com",
                "mobile_web_url": "https://www.naver.com"
            }
        })
    }
    try:
        res = requests.post(url, headers=headers, data=payload, timeout=10)
        if res.status_code == 200 and res.json().get("result_code") == 0:
            print("카카오톡 전송 성공!")
            return True
        else:
            print(f"카카오톡 전송 실패: {res.status_code} {res.text}")
            return False
    except Exception as e:
        print(f"카카오톡 전송 오류: {e}")
        return False


def main():
    print("뉴스 수집 시작...")
    news = fetch_news(RSS_FEEDS)

    total = sum(len(v) for v in news.values())
    print(f"총 {total}개 뉴스 수집 완료")

    message = build_message(news)
    print("\n--- 메시지 미리보기 ---")
    print(message)
    print("----------------------\n")

    send_to_kakao(message, KAKAO_ACCESS_TOKEN)


if __name__ == "__main__":
    main()
