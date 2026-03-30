"""Popga (popga.co.kr) 팝업스토어 크롤러 - 캐릭터/굿즈/애니메이션 카테고리"""

import json
import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://popga.co.kr"

# 캐릭터(40), 일본 애니메이션(68) 카테고리
CATEGORY_IDS = [40, 68]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def build_list_url(category_ids: list[int]) -> str:
    params = "&".join(
        f"categories%5B{i}%5D={cid}" for i, cid in enumerate(category_ids)
    )
    return f"{BASE_URL}/popup/list?{params}"


def extract_popup_ids_from_html(html: str) -> list[int]:
    """__NEXT_F SSR 데이터에서 팝업 ID 목록을 추출한다."""
    popup_ids = []

    # __NEXT_F 스크립트 데이터에서 JSON 파싱
    pattern = re.compile(r'self\.__next_f\.push\(\[.*?"(.*?)"\]\)', re.DOTALL)
    chunks = pattern.findall(html)

    for chunk in chunks:
        # id 필드가 있는 JSON 오브젝트 탐색
        id_matches = re.findall(r'"id"\s*:\s*(\d+)', chunk)
        for id_str in id_matches:
            pid = int(id_str)
            if pid > 100:  # 카테고리 ID(1~100) 제외, 팝업 ID만
                popup_ids.append(pid)

    # href="/popup/{id}" 패턴도 추가로 수집
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=re.compile(r"^/popup/\d+")):
        href = a.get("href", "")
        m = re.search(r"/popup/(\d+)", href)
        if m:
            popup_ids.append(int(m.group(1)))

    # 중복 제거 및 정렬
    return list(dict.fromkeys(popup_ids))


def fetch_popup_detail(popup_id: int) -> dict | None:
    """개별 팝업 상세 페이지에서 텍스트 콘텐츠를 가져온다."""
    url = f"{BASE_URL}/popup/{popup_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Popga] 상세 요청 실패 {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # 주요 콘텐츠 영역 텍스트 추출
    main = soup.select_one("main") or soup.select_one("article") or soup.select_one("body")
    text_content = main.get_text(separator="\n", strip=True) if main else ""

    # __NEXT_F 에서 구조화 데이터 추출 시도
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True).replace(" | 팝가", "").strip()

    return {
        "url": url,
        "text_content": text_content[:8000],
        "source": "Popga",
        "title_hint": title,
    }


def crawl(max_items: int = 30) -> list[dict]:
    """Popga에서 캐릭터/애니메이션 카테고리 팝업을 크롤링한다."""
    list_url = build_list_url(CATEGORY_IDS)

    try:
        resp = requests.get(list_url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Popga] 목록 요청 실패: {e}")
        return []

    popup_ids = extract_popup_ids_from_html(resp.text)
    popup_ids = popup_ids[:max_items]

    if not popup_ids:
        print("[Popga] 팝업 ID를 찾지 못했습니다.")
        return []

    results = []
    for pid in popup_ids:
        detail = fetch_popup_detail(pid)
        if detail:
            results.append(detail)

    print(f"[Popga] {len(results)}개 팝업 크롤링 완료 (캐릭터/애니메이션)")
    return results
