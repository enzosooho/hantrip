"""Claude API를 사용하여 크롤링 데이터를 정제하고 중국어로 번역한다."""

import json
import anthropic

EXTRACTION_PROMPT = """\
아래는 한국 팝업스토어/전시/행사 웹페이지에서 추출한 텍스트입니다.
이 텍스트에서 다음 정보를 JSON 형식으로 추출해주세요.

필수 필드:
- event_name: 행사명 (한국어)
- event_name_cn: 행사명 (중국어 번역)
- organizer: 주최사/브랜드명
- venue: 장소 (구체적 주소 또는 장소명)
- city: 도시 (서울/부산/대구/인천/대전/광주 중 하나, 해당 없으면 "기타")
- start_date: 행사 시작일 (YYYY-MM-DD 형식, 알 수 없으면 null)
- end_date: 행사 종료일 (YYYY-MM-DD 형식, 알 수 없으면 null)
- admission_fee: 입장료 (무료이면 "무료", 유료면 금액, 알 수 없으면 "확인필요")
- parking: 주차 여부 ("가능", "불가", "확인필요" 중 하나)
- description_ko: 행사 상세 설명 (한국어, 2~3문장 요약)
- description_cn: 행사 상세 설명 (중국어 번역, 2~3문장)

중국어 번역은 자연스러운 중문 간체로 작성해주세요.
팝업스토어/전시/행사가 아닌 콘텐츠이면 null을 반환해주세요.
반드시 JSON만 출력하세요. 다른 텍스트는 포함하지 마세요.

---
원본 URL: {url}
소스: {source}

텍스트:
{text}
"""


def extract_and_translate(raw_data: dict, client: anthropic.Anthropic) -> dict | None:
    """크롤링된 raw 데이터에서 구조화된 정보를 추출하고 중국어로 번역한다."""
    prompt = EXTRACTION_PROMPT.format(
        url=raw_data["url"],
        source=raw_data["source"],
        text=raw_data["text_content"],
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    # JSON 블록 추출
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print(f"[LLM] JSON 파싱 실패: {raw_data['url']}")
        return None

    if data is None:
        return None

    # 소스 정보와 URL 추가
    data["source_url"] = raw_data["url"]
    data["source"] = raw_data["source"]
    return data


def process_batch(raw_items: list[dict], api_key: str) -> list[dict]:
    """여러 크롤링 결과를 일괄 처리한다."""
    client = anthropic.Anthropic(api_key=api_key)
    results = []

    for item in raw_items:
        try:
            processed = extract_and_translate(item, client)
            if processed and processed.get("event_name"):
                results.append(processed)
                print(f"[LLM] 처리 완료: {processed['event_name']}")
            else:
                print(f"[LLM] 유효하지 않은 데이터 건너뜀: {item['url']}")
        except Exception as e:
            print(f"[LLM] 처리 실패: {item['url']} - {e}")

    print(f"[LLM] 총 {len(results)}/{len(raw_items)}개 처리 완료")
    return results
