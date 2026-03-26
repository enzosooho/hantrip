"""더현대 (The Hyundai) 팝업스토어/이벤트 크롤러"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.thehyundai.com"
EVENT_URL = f"{BASE_URL}/front/cma/itemPtc/itemPtcList.thd"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def fetch_event_list() -> list[dict]:
    """더현대 이벤트/팝업 목록을 가져온다."""
    resp = requests.get(EVENT_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []
    for link in soup.select("a[href]"):
        href = link.get("href", "")
        if "itemPtcDtl" in href or "popup" in href.lower():
            full_url = href if href.startswith("http") else BASE_URL + href
            title_tag = link.select_one(".tit, .title, h3, h4, strong")
            title = title_tag.get_text(strip=True) if title_tag else link.get_text(strip=True)
            if full_url not in [e["url"] for e in events] and title:
                events.append({"url": full_url, "title_hint": title[:100]})

    return events


def fetch_event_detail(url: str) -> dict:
    """개별 이벤트 상세 페이지에서 raw 텍스트를 가져온다."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    main = soup.select_one(".content, .event-detail, main, article") or soup.select_one("body")
    text_content = main.get_text(separator="\n", strip=True) if main else ""

    return {
        "url": url,
        "html": resp.text,
        "text_content": text_content[:8000],
        "source": "더현대",
    }


def crawl(max_items: int = 20) -> list[dict]:
    """더현대에서 현재 진행 중인 이벤트/팝업을 크롤링한다."""
    events = fetch_event_list()[:max_items]

    results = []
    for item in events:
        try:
            detail = fetch_event_detail(item["url"])
            results.append(detail)
        except Exception as e:
            print(f"[더현대] 상세 크롤링 실패: {item['url']} - {e}")

    print(f"[더현대] {len(results)}개 이벤트 크롤링 완료")
    return results
