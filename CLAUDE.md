# Hantrip 팝업스토어 수집 파이프라인

## 프로젝트 개요
한국 팝업스토어/전시/행사 정보를 매주 월요일 오전 9시(KST)에 자동 수집 → LLM 정제/중국어 번역 → Notion DB 적재하는 파이프라인.

## 구조
```
pipeline/
├── main.py              # 파이프라인 진입점
├── crawlers/
│   ├── popply.py        # Popply 크롤러
│   └── thehyundai.py    # 더현대 크롤러
├── llm_processor.py     # Claude API 정제 + 중국어 번역
├── notion_loader.py     # Notion DB 적재
└── requirements.txt
.github/workflows/
└── collect-popups.yml   # GitHub Actions (매주 월요일 9시 KST)
```

## 실행 방법
```bash
cd pipeline
pip install -r requirements.txt
python main.py
```

## 필요 환경변수
- `ANTHROPIC_API_KEY` — Claude API 키
- `NOTION_API_KEY` — Notion Integration 토큰
- `NOTION_DATABASE_ID` — 대상 Notion DB ID

## 크롤러 추가 방법
1. `pipeline/crawlers/` 에 새 파일 생성
2. `crawl()` 함수 구현 (반환: `list[dict]` with `url`, `text_content`, `source` 키)
3. `main.py`에서 import 후 `raw_data.extend(crawl_new_source())` 추가
