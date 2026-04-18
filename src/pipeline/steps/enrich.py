"""
파이프라인 Step 2: 아이템 보강.

Snippet 모드 아이템에 대해 Full-fetch 수행 여부를 판단하고,
콘텐츠 해시 및 정규화된 텍스트를 생성합니다.
"""
import time
import requests
from typing import Tuple
from src.models import ExtractedItem
from src.config.settings import FULL_FETCH_DOMAINS
from src.processor.hasher import generate_content_hash, normalize_content
from src.pipeline.metrics import PipelineMetrics
from src.utils.logger import get_logger

logger = get_logger(__name__)


def should_full_fetch(item: ExtractedItem) -> bool:
    """아이템에 대해 2차 Full-fetch가 필요한지 판단합니다.

    다음 조건 중 하나라도 해당하면 Full-fetch를 수행합니다:
    1. URL이 FULL_FETCH_DOMAINS 목록의 도메인에 속하는 경우
    2. snippet이 없거나 150자 미만인 경우

    Args:
        item: 판단 대상 아이템

    Returns:
        Full-fetch 필요 여부
    """
    if any(domain in item.url for domain in FULL_FETCH_DOMAINS):
        return True
    if not item.snippet or len(item.snippet) < 150:
        return True
    return False


def enrich_item(item: ExtractedItem, metrics: PipelineMetrics) -> Tuple[str, str]:
    """아이템의 콘텐츠를 보강하고 해시를 생성합니다.

    1. 필요 시 Full-fetch 수행 (rate limiting 포함)
    2. 최종 콘텐츠 해시 생성
    3. 콘텐츠 정규화 텍스트 생성

    Args:
        item: 보강 대상 아이템 (in-place 수정됨)
        metrics: 파이프라인 메트릭 (in-place 업데이트)

    Returns:
        (content_hash, normalized_text) 튜플
    """
    # Full-fetch 수행 (필요 시)
    if item.fetch_mode == "snippet" and should_full_fetch(item):
        logger.info(f"Enriching item via full-fetch: {item.title}")
        try:
            time.sleep(0.5)  # Rate limiting
            resp = requests.get(item.url, timeout=10, headers={"User-Agent": "Knowledge-Bot/1.0"})
            resp.raise_for_status()
            item.raw_content = resp.text[:20000]
            item.fetch_mode = "full"
            metrics.item_full_fetched_count += 1
        except Exception as fe:
            logger.warning(f"Full-fetch failed for {item.url}, using snippet: {fe}")
            metrics.item_parse_failed_count += 1

    # 해시 및 정규화 텍스트 생성
    final_content = item.raw_content or item.snippet or ""
    content_hash = generate_content_hash(final_content)
    normalized_text = normalize_content(final_content)

    return content_hash, normalized_text
