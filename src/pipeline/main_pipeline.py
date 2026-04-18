"""
메인 파이프라인 오케스트레이터.

소스 추출 → 보강 → 저장 → 요약 → 배포의 전체 파이프라인을 조율합니다.
각 단계는 src.pipeline.steps 패키지의 개별 모듈로 분리되어 있습니다.
"""
import os
from src.config.parser import load_sources
from src.config.settings import DB_PATH, SCHEMA_PATH, SOURCES_PATH, INTERESTS_PATH
from src.db.client import init_db, check_duplicate
from src.processor.hasher import generate_url_hash, generate_content_hash, normalize_url
from src.extractor.engines import (
    engine_rss_itemized, engine_hn_listing,
    engine_reddit_listing, engine_rss_fallback
)
from src.processor.scorer import Scorer
from src.pipeline.metrics import PipelineMetrics
from src.pipeline.steps.extract import process_source
from src.pipeline.steps.enrich import enrich_item
from src.pipeline.steps.store import store_item
from src.pipeline.steps.summarize import summarize_item
from src.pipeline.steps.distribute import distribute_results
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_pipeline():
    """전체 파이프라인을 실행합니다.

    실행 흐름:
    1. DB 초기화 (최초 실행 시)
    2. 소스 목록 로드
    3. 각 소스별로:
       a. 아이템 추출
       b. 예비 중복 검사 (불필요한 full-fetch 방지)
       c. 아이템 보강 (full-fetch + 해싱)
       d. 보강 후 중복 재검사 및 DB 저장
       e. LLM 요약 및 스코어링
    4. 실행 요약 로깅
    5. 리포트 생성 및 Discord 알림 발송
    """
    metrics = PipelineMetrics()

    # 1. DB 초기화 (최초 실행 시)
    if not os.path.exists(DB_PATH):
        logger.info("Initializing database...")
        init_db(DB_PATH, SCHEMA_PATH)

    # 2. 소스 로드
    sources = load_sources(SOURCES_PATH)
    metrics.source_count = len(sources)
    logger.info(f"Loaded {len(sources)} sources.")

    # 3. 엔진 및 스코어러 설정
    extraction_engines = [
        engine_rss_itemized,
        engine_hn_listing,
        engine_reddit_listing,
        engine_rss_fallback
    ]
    scorer = Scorer(INTERESTS_PATH)

    # 4. 소스별 처리
    for source in sources:
        items = process_source(source, extraction_engines, metrics)

        for item in items:
            try:
                # 4a. URL 정규화 및 해시 생성
                item.canonical_url = item.canonical_url or normalize_url(item.url)
                url_hash = generate_url_hash(item.url)

                # 4b. 예비 중복 검사 (불필요한 full-fetch 방지)
                initial_content = item.raw_content or item.snippet or ""
                if check_duplicate(DB_PATH, url_hash, generate_content_hash(initial_content)):
                    metrics.item_duplicate_count += 1
                    continue

                # 4c. 아이템 보강 (full-fetch + 최종 해시 생성)
                content_hash, normalized_text = enrich_item(item, metrics)

                # 4d. 보강 후 중복 재검사
                if check_duplicate(DB_PATH, url_hash, content_hash):
                    metrics.item_duplicate_count += 1
                    continue

                # 4e. 상태 판정 및 DB 저장
                article_id, status = store_item(
                    item, url_hash, content_hash, normalized_text,
                    source.id, metrics
                )
                if article_id is None:
                    continue

                # 4f. LLM 요약 및 스코어링 (NEW/UPDATED만)
                if status in ["NEW", "UPDATED"]:
                    final_content = item.raw_content or item.snippet or ""
                    summarize_item(
                        article_id, item, final_content,
                        scorer, source.source_weight, item.fetch_mode, metrics
                    )

            except Exception as e:
                logger.error(f"Error processing item {item.url}: {e}")
                metrics.errors += 1

    # 5. 실행 요약 로깅
    _log_summary(metrics)

    # 6. 리포트 생성 및 Discord 알림 발송
    distribute_results(metrics)

    logger.info("Pipeline execution completed.")


def _log_summary(metrics: PipelineMetrics):
    """파이프라인 실행 요약을 로깅합니다.

    Args:
        metrics: 파이프라인 실행 메트릭
    """
    logger.info("--- Pipeline Execution Summary ---")
    for k, v in metrics.to_dict().items():
        logger.info(f"{k.replace('_', ' ').title()}: {v}")

    if metrics.stored_new == 0 and metrics.stored_updated == 0:
        if metrics.fetched > 0:
            logger.info("Pipeline completed successfully, but no new/updated data found.")
        else:
            logger.error("Pipeline finished with 0 fetches. Check connectivity or sources config.")


if __name__ == "__main__":
    run_pipeline()
