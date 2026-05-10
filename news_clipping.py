import feedparser
import requests
from datetime import datetime
import os

KAKAO_ACCESS_TOKEN = os.environ.get("KAKAO_ACCESS_TOKEN", "")

RSS_FEEDS = {
    "유통/백화점": [
        "https://www.hankyung.com/feed/distribution",
        "https://www.mk.co.kr/rss/50400012/",
        "https://www.sedaily.com/NewsList/GF/rss",
    ],
    "AI/테크": [
        "https://www.aitimes.com/rss/allArticle.xml",
        "https://zdnet.co.kr/rss/",
        "https://www.itdaily.kr/rss/allArticle.xml",
    ],
    "교육/HRD": [
        "https://www.eduinnews.co.kr/rss/allArticle.xml",
        "https://www.edujin.co.kr/rss/allArticle.xml",
        "https://www.hrdkorea.or.kr/rss/rssNews.do",
    ],
    "주식/경제": [
        "https://www.mk.co.kr/rss/30300001/",
        "https://www.hankyung.com/feed/economy",
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
    "교육/HRD": [
        "교육", "HRD", "연수", "직무교육", "이러닝", "e러닝",
        "학습", "인재개발", "역량", "강의", "훈련", "교원"
    ],
    "주식/경제": [
        "주식", "증시", "코스피", "코스닥", "금리", "환율", "경제",
        "투자", "펀드", "ETF", "채권", "기준금리"
    ],
}

NEWS_PER_CATEGORY = 3
MAX_TITLE_LENGTH = 40


def fetch_news(feeds):
    result = {}
    for category, urls in feeds.items():
        items = []
        keywords = KEYWORDS.get(category, [])
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    title = entry.get("title", "").strip()
                    link = entry.get("link", "").strip()
                    if not title or not link:
                        continue
                    if keywords and not any(kw in title for kw in keywords):
                        continue
                    if len(title) > MAX_TITLE_LENGTH:
                        title = title[:MAX_TITLE_LENGTH] + "..."
                    items.append({"title": title, "link": link})
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
