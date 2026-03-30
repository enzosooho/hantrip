"""Hantrip 팝업스토어 수집 파이프라인 - 메인 실행 스크립트"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from crawlers.popply import crawl as crawl_popply
from crawlers.thehyundai import crawl as crawl_thehyundai
from crawlers.popga import crawl as crawl_popga
from llm_processor import process_batch
from notion_loader import load_to_notion


def main():
    load_dotenv()

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    notion_key = os.environ.get("NOTION_API_KEY")
    notion_db_id = os.environ.get("NOTION_DATABASE_ID")

    if not all([anthropic_key, notion_key, notion_db_id]):
        print("ERROR: ANTHROPIC_API_KEY, NOTION_API_KEY, NOTION_DATABASE_ID 환경변수를 설정하세요.")
        sys.exit(1)

    print(f"=== Hantrip 팝업스토어 수집 시작: {datetime.now().isoformat()} ===\n")

    # 1. 크롤링
    print("--- [1/3] 크롤링 ---")
    raw_data = []

    try:
        raw_data.extend(crawl_popply(max_pages=2, max_items=30))
    except Exception as e:
        print(f"[Popply] 크롤러 오류: {e}")

    try:
        raw_data.extend(crawl_thehyundai(max_items=20))
    except Exception as e:
        print(f"[더현대] 크롤러 오류: {e}")

    try:
        raw_data.extend(crawl_popga(max_items=30))
    except Exception as e:
        print(f"[Popga] 크롤러 오류: {e}")

    if not raw_data:
        print("수집된 데이터가 없습니다. 파이프라인을 종료합니다.")
        sys.exit(0)

    print(f"\n총 {len(raw_data)}개 raw 데이터 수집 완료\n")

    # 2. LLM 정제 + 중국어 번역
    print("--- [2/3] LLM 정제 및 번역 ---")
    processed_data = process_batch(raw_data, anthropic_key)

    if not processed_data:
        print("정제된 데이터가 없습니다. 파이프라인을 종료합니다.")
        sys.exit(0)

    print(f"\n총 {len(processed_data)}개 정제 완료\n")

    # 3. Notion DB 적재
    print("--- [3/3] Notion DB 적재 ---")
    created = load_to_notion(processed_data, notion_key, notion_db_id)

    print(f"\n=== 파이프라인 완료: {created}건 신규 적재 ===")


if __name__ == "__main__":
    main()
