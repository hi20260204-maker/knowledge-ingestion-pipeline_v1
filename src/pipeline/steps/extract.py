"""
파이프라인 Step 1: 소스 추출.

각 소스에서 아이템을 추출하고, 레거시 단일 콘텐츠를 아이템으로 변환합니다.
"""
from typing import List
from src.models import ExtractedItem, ExtractorFunc
from src.models.config import SourceConfig
from src.extractor.base import perform_extraction
from src.pipeline.metrics import PipelineMetrics
from src.utils.logger import get_logger

logger = get_logger(__name__)


def process_source(source: SourceConfig, engines: List[ExtractorFunc],
                   metrics: PipelineMetrics) -> List[ExtractedItem]:
    """단일 소스에서 아이템을 추출합니다.

    추출 엔진 체인을 통해 소스 URL에서 아이템을 가져옵니다.
    아이템이 없지만 단일 콘텐츠가 있는 경우 레거시 호환을 위해
    단일 ExtractedItem으로 변환합니다.

    Args:
        source: 소스 설정 (SourceConfig)
        engines: 추출 엔진 목록
        metrics: 파이프라인 메트릭 (in-place 업데이트)

    Returns:
        추출된 ExtractedItem 목록
    """
    logger.info(f"Processing source: {source.id} ({source.url})")
    extraction_result = perform_extraction(source.url, engines)
    metrics.fetched += 1

    if not extraction_result.success:
        logger.error(f"Failed to extract from {source.url}: {extraction_result.error}")
        metrics.errors += 1
        return []

    items = extraction_result.items

    # 레거시 호환: 아이템이 없지만 단일 콘텐츠가 있는 경우 변환
    if not items and extraction_result.content:
        items = [ExtractedItem(
            title=extraction_result.title or f"Article from {source.id}",
            url=extraction_result.url or source.url,
            raw_content=extraction_result.content,
            source_name=source.id,
            source_type="legacy_fallback",
            fetch_mode="full"
        )]

    metrics.item_extracted_count += len(items)
    return items
