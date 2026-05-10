import feedparser
import requests
from datetime import datetime
import os

KAKAO_ACCESS_TOKEN = os.environ.get("KAKAO_ACCESS_TOKEN", "")

RSS_FEEDS = {
    "유통/백화점": [
        "https://www.hankyung.com/feed/distribution",        # 한국경제 유통
        "https://www.mk.co.kr/rss/50400012/",               # 매경 유통
        "https://www.sedaily.com/NewsList/GF/rss",           # 서울경제 유통
    ],
    "AI/테크": [
        "https://www.aitimes.com/rss/allArticle.xml",        # AI타임스 (AI 전문)
        "https://www.itdaily.kr/rss/allArticle.xml",         # IT데일리
        "https://zdnet.co.kr/rss/",                          # ZDNet Korea
    ],
    "교육/HRD": [
        "https://www.hrdkorea.or.kr/rss/rssNews.do",         # HRD Korea 공식
        "https://www.eduinnews.co.kr/rss/allArticle.xml",    # 에듀인뉴스 (교육 전문)
        "https://www.edujin.co.kr/rss/allArticle.xml",       # 에듀진 (교육 전문)
    ],
    "주식/경제": [
        "https://www.mk.co.kr/rss/30300001/",                # 매경 증권
        "https://www.hankyung.com/feed/economy",             # 한국경제 경제
        "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258", # 네이버 증권
    ],
}

NEWS_PER_CATEGORY = 3
MAX_TITLE_LENGTH = 40

# ============================================================


def fetch_news(feeds):
    result = {}
    for category, urls in feeds.items():
        items = []
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:NEWS_PER_CATEGORY]:
                    title = entry.get("title", "제목 없음").strip()
                    link = entry.get("link", "").strip()
                    if title and link:
                        if len(title) > MAX_TITLE_LENGTH:
                            title = title[:MAX_TITLE_LENGTH] + "..."
                        items.append({"title": title, "link": link})
                if items:
                    break
            except Exception as e:
                print(f"[오류] {category} - {url}: {e}")
                continue
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
