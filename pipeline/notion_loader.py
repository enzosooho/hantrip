"""정제된 팝업스토어 데이터를 Notion DB에 적재한다."""

from datetime import datetime, date
from notion_client import Client


def build_page_properties(item: dict) -> dict:
    """정제된 데이터를 Notion 페이지 속성으로 변환한다."""
    props = {
        "행사명": {"title": [{"text": {"content": item.get("event_name", "")}}]},
        "행사명 (중문)": {"rich_text": [{"text": {"content": item.get("event_name_cn", "")}}]},
        "주최사": {"rich_text": [{"text": {"content": item.get("organizer", "")}}]},
        "장소": {"rich_text": [{"text": {"content": item.get("venue", "")}}]},
        "입장료": {"rich_text": [{"text": {"content": item.get("admission_fee", "확인필요")}}]},
        "원본 URL": {"url": item.get("source_url")},
        "행사 상세 (한국어)": {
            "rich_text": [{"text": {"content": item.get("description_ko", "")[:2000]}}]
        },
        "행사 상세 (중국어)": {
            "rich_text": [{"text": {"content": item.get("description_cn", "")[:2000]}}]
        },
        "수집일": {"date": {"start": date.today().isoformat()}},
    }

    # 도시 (select)
    city = item.get("city", "기타")
    valid_cities = ["서울", "부산", "대구", "인천", "대전", "광주", "기타"]
    props["도시"] = {"select": {"name": city if city in valid_cities else "기타"}}

    # 주차 여부 (select)
    parking = item.get("parking", "확인필요")
    valid_parking = ["가능", "불가", "확인필요"]
    props["주차 여부"] = {"select": {"name": parking if parking in valid_parking else "확인필요"}}

    # 소스 (select)
    source = item.get("source", "기타")
    valid_sources = ["Popply", "더현대", "신세계", "기타"]
    props["소스"] = {"select": {"name": source if source in valid_sources else "기타"}}

    # 행사 시작일
    if item.get("start_date"):
        props["행사 시작일"] = {"date": {"start": item["start_date"]}}

    # 행사 종료일
    if item.get("end_date"):
        props["행사 종료일"] = {"date": {"start": item["end_date"]}}

    return props


def get_existing_urls(notion: Client, database_id: str) -> set[str]:
    """이미 DB에 있는 URL 목록을 가져와 중복 적재를 방지한다."""
    existing = set()
    cursor = None

    while True:
        query_params = {"database_id": database_id, "page_size": 100}
        if cursor:
            query_params["start_cursor"] = cursor

        response = notion.databases.query(**query_params)

        for page in response["results"]:
            url_prop = page["properties"].get("원본 URL", {})
            if url_prop.get("url"):
                existing.add(url_prop["url"])

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return existing


def load_to_notion(items: list[dict], api_key: str, database_id: str) -> int:
    """정제된 데이터를 Notion DB에 적재한다. 중복 URL은 건너뛴다."""
    notion = Client(auth=api_key)

    existing_urls = get_existing_urls(notion, database_id)
    print(f"[Notion] 기존 데이터 {len(existing_urls)}건 확인")

    created = 0
    for item in items:
        source_url = item.get("source_url", "")
        if source_url in existing_urls:
            print(f"[Notion] 중복 건너뜀: {item.get('event_name', '')}")
            continue

        try:
            properties = build_page_properties(item)
            notion.pages.create(
                parent={"database_id": database_id},
                properties=properties,
            )
            created += 1
            print(f"[Notion] 적재 완료: {item.get('event_name', '')}")
        except Exception as e:
            print(f"[Notion] 적재 실패: {item.get('event_name', '')} - {e}")

    print(f"[Notion] 총 {created}건 신규 적재 (중복 {len(items) - created}건 건너뜀)")
    return created
