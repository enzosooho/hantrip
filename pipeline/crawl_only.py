"""크롤러만 실행하여 JSON으로 결과를 출력하는 스크립트.
Claude Code 원격 트리거에서 사용한다.
"""

import json
import sys

from crawlers.popply import crawl as crawl_popply
from crawlers.thehyundai import crawl as crawl_thehyundai


def main():
    raw_data = []

    try:
        raw_data.extend(crawl_popply(max_pages=2, max_items=30))
    except Exception as e:
        print(f"[Popply] 크롤러 오류: {e}", file=sys.stderr)

    try:
        raw_data.extend(crawl_thehyundai(max_items=20))
    except Exception as e:
        print(f"[더현대] 크롤러 오류: {e}", file=sys.stderr)

    # HTML 필드 제거 (JSON 크기 축소)
    for item in raw_data:
        item.pop("html", None)

    print(json.dumps(raw_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
