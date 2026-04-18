"""
파이프라인 Step 3: 상태 판정 및 DB 저장.

콘텐츠 품질 검사, 상태 판정(NEW/UPDATED/LOW_QUALITY), DB 저장을 수행합니다.
"""
from typing import Optional, Tuple
from src.models import ExtractedItem
from src.config.settings import DB_PATH, QUALITY_THRESHOLD_CHARS
from src.db.client import save_article, find_latest_article_id
from src.pipeline.metrics import PipelineMetrics
from src.utils.logger import get_logger

logger = get_logger(__name__)


def store_item(item: ExtractedItem, url_hash: str, content_hash: str,
               normalized_text: str, source_id: str,
               metrics: PipelineMetrics) -> Tuple[Optional[int], Optional[str]]:
    """아이템의 상태를 판정하고 DB에 저장합니다.

    1. 저품질 콘텐츠 필터링 (QUALITY_THRESHOLD_CHARS 미만)
    2. 기존 URL의 콘텐츠 변경 감지 (UPDATED 상태 판정)
    3. articles 테이블에 레코드 삽입
    4. 메트릭 업데이트

    Note: 중복 검사(check_duplicate)는 호출 전에 main_pipeline에서 수행됩니다.

    Args:
        item: 저장할 아이템
        url_hash: URL 해시
        content_hash: 콘텐츠 해시
        normalized_text: 정규화된 텍스트
        source_id: 소스 ID
        metrics: 파이프라인 메트릭 (in-place 업데이트)

    Returns:
        (article_id, status) 튜플. 저품질인 경우에도 저장됨.
    """
    # 상태 판정
    status = "NEW"
    parent_id = None

    if len(normalized_text) < QUALITY_THRESHOLD_CHARS:
        status = "LOW_QUALITY"
        metrics.item_low_quality_count += 1
    else:
        existing_id = find_latest_article_id(DB_PATH, url_hash)
        if existing_id:
            status = "UPDATED"
            parent_id = existing_id

    # DB 저장
    final_content = item.raw_content or item.snippet or ""
    article_data = {
        'source_id': source_id,
        'raw_url': item.url,
        'canonical_url': item.canonical_url,
        'title': item.title,
        'url_hash': url_hash,
        'content_hash': content_hash,
        'raw_content': final_content,
        'status': status,
        'parent_id': parent_id
    }

    article_id = save_article(DB_PATH, article_data)

    if status == "NEW":
        metrics.stored_new += 1
    elif status == "UPDATED":
        metrics.stored_updated += 1

    return article_id, status
