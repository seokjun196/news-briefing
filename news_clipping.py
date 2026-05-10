import feedparser
import requests
from datetime import datetime
import os

KAKAO_REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY", "")
KAKAO_REFRESH_TOKEN = os.environ.get("KAKAO_REFRESH_TOKEN", "")

def get_access_token():
    res = requests.post("https://kauth.kakao.com/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": KAKAO_REST_API_KEY,
        "refresh_token": KAKAO_REFRESH_TOKEN,
    })
    return res.json().get("access_token")

KAKAO_ACCESS_TOKEN = get_access_token()

RSS_FEEDS = {
    "유통/백화점": [
        "https://www.sedaily.com/NewsList/GF/rss",
        "https://www.hankyung.com/feed/distribution",
    ],
    "AI/테크": [
        "https://www.aitimes.com/rss/allArticle.xml",
        "https://zdnet.co.kr/rss/",
    ],
    "교육/HRD": [
        "https://www.edaily.co.kr/rss/newsflash.xml",
        "https://rss.etnews.com/Section901.xml",
    ],
    "주식/경제": [
        "https://www.mk.co.kr/rss/40300001/",
        "https://www.hankyung.com/feed/economy",
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
