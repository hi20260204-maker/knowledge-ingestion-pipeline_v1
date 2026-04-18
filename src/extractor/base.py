"""
추출 엔진 오케스트레이터.

여러 추출 엔진을 순차적으로 실행하여 첫 번째 성공 결과를 반환하는
Fallback 패턴을 구현합니다.
"""
from typing import List
from src.models import ExtractionResult, ExtractorFunc
from src.utils.logger import get_logger

logger = get_logger(__name__)


def perform_extraction(url: str, engines: List[ExtractorFunc]) -> ExtractionResult:
    """등록된 추출 엔진들을 순차적으로 실행하여 콘텐츠를 추출합니다.

    첫 번째로 성공하는 엔진의 결과를 반환합니다.
    모든 엔진이 실패하면 마지막 에러를 포함한 실패 결과를 반환합니다.

    Args:
        url: 추출 대상 URL
        engines: 순서대로 시도할 추출 엔진 함수 목록

    Returns:
        ExtractionResult: 추출 결과 (성공 또는 실패)
    """
    last_error = "No extraction engines provided."

    for engine in engines:
        engine_name = engine.__name__
        try:
            result = engine(url)
            if result.success:
                logger.info(f"Successfully extracted {url} using {engine_name}")
                result.used_engine = engine_name
                return result
            else:
                last_error = result.error or "Unknown extraction error."
                logger.warning(f"Engine {engine_name} failed for {url}: {last_error}")
        except Exception as e:
            last_error = str(e)
            logger.error(f"Engine {engine_name} raised exception for {url}: {last_error}")

    return ExtractionResult(success=False, error=f"All engines failed. Last error: {last_error}")
