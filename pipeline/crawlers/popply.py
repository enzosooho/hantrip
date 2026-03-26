"""Popply (popply.co.kr) 팝업스토어 크롤러"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime


BASE_URL = "https://popply.co.kr"
LIST_URL = f"{BASE_URL}/popup/list"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def fetch_popup_list(page: int = 1) -> list[dict]:
    """Popply 팝업 목록 페이지에서 개별 팝업 URL을 수집한다."""
    resp = requests.get(
        LIST_URL,
        params={"page": page},
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    popups = []
    # Popply 카드 링크 패턴
    for card in soup.select("a[href*='/popup/']"):
        href = card.get("href", "")
        if "/popup/" in href and href != "/popup/list":
            full_url = href if href.startswith("http") else BASE_URL + href
            if full_url not in [p["url"] for p in popups]:
                popups.append({"url": full_url})

    return popups


def fetch_popup_detail(url: str) -> dict:
    """개별 팝업 상세 페이지에서 raw HTML을 가져온다."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 메인 콘텐츠 영역 텍스트 추출
    main = soup.select_one("main") or soup.select_one("body")
    text_content = main.get_text(separator="\n", strip=True) if main else ""

    return {
        "url": url,
        "html": resp.text,
        "text_content": text_content[:8000],  # LLM 입력 길이 제한
        "source": "Popply",
    }


def crawl(max_pages: int = 2, max_items: int = 30) -> list[dict]:
    """Popply에서 현재 진행 중인 팝업 목록을 크롤링한다."""
    all_urls = []
    for page in range(1, max_pages + 1):
        urls = fetch_popup_list(page)
        all_urls.extend(urls)
        if not urls:
            break

    all_urls = all_urls[:max_items]

    results = []
    for item in all_urls:
        try:
            detail = fetch_popup_detail(item["url"])
            results.append(detail)
        except Exception as e:
            print(f"[Popply] 상세 크롤링 실패: {item['url']} - {e}")

    print(f"[Popply] {len(results)}개 팝업 크롤링 완료")
    return results
