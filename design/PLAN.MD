# IT 뉴스 및 테크 블로그 요약 파이프라인 (PLAN 3.0 - Phase 4 Refactored)

## 1. 프로젝트 개요
IT 이슈 및 테크 블로그 소식을 자동으로 파악하기 위한 **엔지니어링 중심의 지식 자동화 파이프라인**입니다. 단순 크롤링을 넘어, 중복 알림 방지의 정밀도, 무결성 관리, 토큰 비용 최적화를 최우선으로 고려합니다.

---

## 2. 시스템 아키텍처 및 데이터 흐름

### **2.1 파이프라인 상세**
1. **Ingestion (Step 1: Extract):**
    * `config/sources.yaml` 파싱. 모든 소스는 `source_id` 기준 Unique성을 강제 관리합니다.
    * 소스별 추출: `engine_rss_itemized` → `engine_hn_listing` → `engine_reddit_listing` → `engine_rss_fallback` 순 Fallback
2. **Deduplication (다중 해시 기반):**
    * **Pre-Enrichment Check:** 정규화된 URL 기반 `url_hash` + 초기 콘텐츠 `content_hash`
    * **Post-Enrichment Check:** Full-fetch 후 최종 콘텐츠 기반 `content_hash` 재검사
    * URL 정규화: utm 파라미터 제거, 도메인별 특화 규칙 (Reddit/HN)
    * Content 정규화: HTML 태그 제거 → 노이즈 제거 → 소문자 변환 → 전체 본문 SHA-256
3. **Enrichment (Step 2: Enrich):**
    * `should_full_fetch()` 판단: 주요 도메인 블로그 또는 snippet < 150자인 경우 전체 본문 fetch
    * Rate limiting (0.5초 간격)
4. **Intelligence (Step 4: Summarize):**
    * **Structured LLM:** OpenAI `gpt-4o-mini` + Pydantic Structured Output
    * **Mode-aware:** Snippet 모드(보수적) vs Full 모드(심층 분석) 구분
    * **Dual-Score:** Global Score(기술적 중요도) + Personalized Score(관심사 매칭)
    * **비용 최적화:** 동일 콘텐츠 해시의 기존 요약 재사용
5. **Distribution (Step 5: Distribute):**
    * Markdown 리포트: 토픽별 그룹화, [NEW]/[UPDATED] 상태 태그
    * Discord 알림: G1(Global 1위) + P2(Personal 상위 2건) 하이라이트
    * GitHub Actions 일 1회 배치 (22:00 UTC / 07:00 KST) + 수동 트리거

---

## 3. 프로젝트 구조

```
knowledge-ingestion-pipeline/
├── .github/workflows/daily_batch.yml   # GitHub Actions 자동 배치
├── config/                              # 설정 파일
│   ├── sources.yaml                     # 소스 목록
│   └── interests.yaml                   # 관심사 설정 (high/medium/low)
├── design/                              # 설계 문서
│   ├── PLAN.MD                          # 이 문서
│   └── LINKS.MD                         # 참고 링크
├── docs/                                # 자동 생성 일일 리포트
├── src/
│   ├── models/                          # 데이터 모델 중앙 관리
│   │   ├── extraction.py                # ExtractedItem, ExtractionResult
│   │   ├── summary.py                   # LLMSummaryResponse
│   │   ├── config.py                    # SourceConfig
│   │   └── report.py                    # GroupedReportItem
│   ├── config/
│   │   ├── parser.py                    # sources.yaml 파서
│   │   └── settings.py                  # 중앙 설정 (경로, 상수, 환경변수)
│   ├── db/
│   │   ├── client.py                    # SQLite CRUD (Context Manager 기반)
│   │   └── schema.sql                   # DB 스키마
│   ├── extractor/
│   │   ├── base.py                      # Fallback 오케스트레이터
│   │   └── engines/                     # 소스별 추출 엔진
│   │       ├── rss.py                   # RSS 피드 파서 + HTTP 폴백
│   │       ├── hackernews.py            # HN 인덱스 파서
│   │       └── reddit.py               # Reddit 서브레딧 파서
│   ├── llm/
│   │   └── summarizer.py               # OpenAI Structured Output 요약
│   ├── pipeline/
│   │   ├── main_pipeline.py             # 오케스트레이터 (~100줄)
│   │   ├── metrics.py                   # PipelineMetrics 데이터클래스
│   │   └── steps/                       # 단계별 처리 로직
│   │       ├── extract.py               # Step 1: 소스 추출
│   │       ├── enrich.py                # Step 2: Full-fetch + 해싱
│   │       ├── store.py                 # Step 3: 상태 판정 + DB 저장
│   │       ├── summarize.py             # Step 4: LLM 요약 + 스코어링
│   │       └── distribute.py            # Step 5: 리포트 + 알림
│   ├── processor/
│   │   ├── aggregator.py                # 토픽별 그룹화
│   │   ├── hasher.py                    # URL/콘텐츠 정규화 + SHA-256
│   │   └── scorer.py                    # Dual-Score 계산 엔진
│   ├── distribution/
│   │   ├── reporter.py                  # Markdown 리포트 생성
│   │   └── discord_notifier.py          # Discord 웹훅 알림
│   └── utils/
│       └── logger.py                    # 통합 로깅 설정
├── tests/                               # src/ 미러링 테스트
├── tools/migrations/                    # DB 마이그레이션 스크립트
├── run.py                               # 진입점
├── knowledge.db                         # SQLite DB
└── requirements.txt                     # Python 의존성
```

---

## 4. 데이터베이스 및 스키마 설계

### **Table: articles (수집 원본 유지 계층)**
- `id` (PK), `source_id` (YAML과 매핑)
- `raw_url`, `canonical_url` (정규화), `display_url`
- `title`, `url_hash`, `content_hash`
- `published_at` (UTC)
- `raw_content`, `clean_content`
- `status`: NEW, UPDATED, LOW_QUALITY, SUMMARY_REUSED
- `parent_id`: 리니지 추적 (이전 버전 참조)
- `updated_at`

### **Table: summaries (AI 지능 계층)**
- `id` (PK), `article_id` (FK, UNIQUE)
- `importance_score` (레거시 1-10 스케일)
- `global_score` (0-100, 기술적 중요도)
- `personalized_score` (0-100, 관심사 매칭)
- `reason` (점수 산정 이유)
- `summary_text`, `key_points`, `keywords` (JSON)
- `summary_version`, `created_at`

### **Table: pipeline_logs (관찰성 계층)**
- `id` (PK), `article_id` (FK, Nullable), `target_url`
- `stage`, `status`, `retry_count`, `last_attempt`, `error_message`, `resolved_at`
- `processing_duration_ms`

---

## 5. 설계 결정 기록 (ADR)

### **ADR 1: SQLite 파일의 Git 저장**
* **결정:** MVP 인프라 무과금을 위해 채택. Action의 Concurrency 제한 강제.
* **리스크:** DB 규모 팽창 시 외부 PostgreSQL 마이그레이션 필요.

### **ADR 2: 모델 중앙화 (src/models/)**
* **결정:** 순환 참조 방지 및 재사용성을 위해 모든 데이터 모델을 models/ 패키지에 집중.
* **효과:** 각 모듈 간 의존성이 models/ → 각 모듈 방향으로 단방향화됨.

### **ADR 3: Pipeline Step 분리**
* **결정:** 250줄 God Function을 5개 독립 Step 모듈로 분리.
* **근거:** 단일 책임 원칙, 개별 Step 단위 테스트 용이성, 향후 Step 추가/교체 유연성.

### **ADR 4: Context Manager 기반 DB 연결 관리**
* **결정:** 모든 DB 접근에 `get_connection()` Context Manager 적용.
* **효과:** 예외 시 자동 롤백, 연결 누수 방지.

### **ADR 5: Dual-Score 체계**
* **결정:** Global Score(기술적 중요도) + Personalized Score(관심사 매칭) 이원화.
* **근거:** 객관적 기술 중요도와 주관적 관심사를 분리하여 다양한 큐레이션 전략 지원.

---

## 6. 단계별 로드맵

### **Phase 1: 데이터 무결성 파이프라인 (MVP Core)** ✅
- [x] Unique `source_id` 관리 `sources.yaml` 파서
- [x] DB 스키마(Articles/Summaries/Logs) 연동
- [x] 정밀 해시 룰(`url_hash`, `content_hash`) 및 Fallback 엔진

### **Phase 2: LLM 요약 및 자동화 (MVP Logic)** ✅
- [x] Structured Output 기반 LLM 요약
- [x] GitHub Actions 일일 배치 + 수동 트리거
- [x] Markdown 아카이빙 및 Discord 알림

### **Phase 3: 코드 안정성 확보** ✅
- [x] 유닛 테스트 (config, db, extractor, llm, processor, distribution)
- [x] 통합 로깅 시스템

### **Phase 4: 고정밀 큐레이션 엔진** ✅
- [x] URL 정규화 + 의미론적 콘텐츠 해싱
- [x] Dual-Score 체계 (Global + Personalized)
- [x] G1+P2 선별 로직 Discord 출력
- [x] 토픽별 그룹화 Markdown 리포트

### **Phase 5: 구조 리팩토링** ✅
- [x] `__init__.py` 전체 추가 (Python 패키지 정규화)
- [x] 데이터 모델 중앙화 (`src/models/`)
- [x] Pipeline Step 분리 (`src/pipeline/steps/`)
- [x] DB Context Manager 적용
- [x] Extractor 엔진 분리 (`src/extractor/engines/`)
- [x] 중앙 설정 모듈 (`src/config/settings.py`)
- [x] 데드 의존성 제거, 로거 통일, 메트릭 이중 카운팅 수정

### **Phase 6: 장기 안정성 확보 (Future)**
- [ ] Semantic Similarity 기반 중복 검출 (해시 충돌 한정)
- [ ] DB 저장소 거대화 대응 (압축 옵션)
- [ ] PostgreSQL 마이그레이션
- [ ] RAG 에이전트 연동