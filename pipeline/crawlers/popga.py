"""Popga (popga.co.kr) 팝업스토어 크롤러 - 캐릭터/애니메이션 카테고리

전략:
1. 사이트맵(/sitemap/2.xml)에서 최신 팝업 ID 수집
2. 각 상세 페이지의 OG 메타 태그에서 제목/설명/키워드 추출
3. 캐릭터/굿즈/애니메이션 관련 키워드로 필터링
"""

import json
import re
from typing import Optional, List
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://popga.co.kr"
SITEMAP_URL = f"{BASE_URL}/sitemap/2.xml"

# 캐릭터/굿즈/애니메이션 관련 필터 키워드
CATEGORY_KEYWORDS = [
    "캐릭터", "굿즈", "애니메이션", "애니", "콜라보", "collaboration",
    "manga", "anime", "figure", "피규어", "게임", "아이돌", "idol",
    "포켓몬", "헬로키티", "산리오", "스누피", "카카오", "라인프렌즈",
    "원피스", "나루토", "귀멸", "주술회전", "드래곤볼",
    "마블", "디즈니", "픽사", "짱구", "코난",
    "vtuber", "hatsune", "miku", "초음파", "하츠네",
    "케이팝", "kpop", "bts", "aespa", "stray kids", "nct",
    "블랙핑크", "트와이스", "세븐틴", "엑소",
    "팝업스토어", "pop-up", "pop up", "limited",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def fetch_popup_ids_from_sitemap(limit: int = 200) -> List[int]:
    """사이트맵에서 최신 팝업 ID를 수집한다."""
    try:
        resp = requests.get(SITEMAP_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Popga] 사이트맵 요청 실패: {e}")
        return []

    ids = re.findall(r'popga\.co\.kr/popup/(\d+)', resp.text)
    # 중복 제거 + 최신순(높은 ID) 정렬
    unique_ids = sorted(set(int(i) for i in ids), reverse=True)
    return unique_ids[:limit]


def fetch_popup_meta(popup_id: int) -> Optional[dict]:
    """개별 팝업 상세 페이지에서 OG 메타 태그 정보를 추출한다."""
    url = f"{BASE_URL}/popup/{popup_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Popga] 요청 실패 {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    def meta(name=None, prop=None):
        if name:
            tag = soup.find("meta", attrs={"name": name})
        else:
            tag = soup.find("meta", attrs={"property": prop})
        return tag.get("content", "").strip() if tag else ""

    title = meta(prop="og:title").replace(" | 팝가 Popga", "").replace(" | 팝가", "").strip()
    description = meta(prop="og:description") or meta(name="description")
    keywords = meta(name="keywords")

    if not title:
        return None

    # __NEXT_F 스크립트에서 openDate/closeDate 추출
    open_date, close_date = None, None
    match = re.search(r'openDate\\*"?\s*:\s*\\*"?(\d{4}-\d{2}-\d{2})', resp.text)
    if match:
        open_date = match.group(1)
    match = re.search(r'closeDate\\*"?\s*:\s*\\*"?(\d{4}-\d{2}-\d{2})', resp.text)
    if match:
        close_date = match.group(1)

    # 관련 텍스트 조합
    date_info = ""
    if open_date:
        date_info += f"\n시작일: {open_date}"
    if close_date:
        date_info += f"\n종료일: {close_date}"
    text_content = f"행사명: {title}\n설명: {description}\n키워드: {keywords}{date_info}\n원본URL: {url}"

    return {
        "url": url,
        "text_content": text_content[:8000],
        "source": "Popga",
        "title_hint": title,
        "keywords": keywords,
        "open_date": open_date,
        "close_date": close_date,
    }


def is_relevant(item: dict) -> bool:
    """캐릭터/굿즈/애니메이션 관련 팝업인지 확인한다."""
    text = (item.get("title_hint", "") + " " + item.get("keywords", "")).lower()
    return any(kw.lower() in text for kw in CATEGORY_KEYWORDS)


def crawl(max_items: int = 30, filter_category: bool = True) -> List[dict]:
    """Popga에서 팝업을 크롤링한다.

    filter_category=True이면 캐릭터/굿즈/애니메이션만 수집.
    False이면 전체 수집.
    """
    # 사이트맵에서 최신 ID 수집 (필터링을 위해 여유 있게 수집)
    candidate_limit = max_items * 5 if filter_category else max_items
    popup_ids = fetch_popup_ids_from_sitemap(limit=min(candidate_limit, 300))

    if not popup_ids:
        print("[Popga] 팝업 ID를 찾지 못했습니다.")
        return []

    results = []
    for pid in popup_ids:
        if len(results) >= max_items:
            break

        item = fetch_popup_meta(pid)
        if not item:
            continue

        if filter_category and not is_relevant(item):
            continue

        results.append(item)
        print(f"[Popga] 수집: {item['title_hint']}")

    print(f"[Popga] {len(results)}개 팝업 크롤링 완료")
    return results
