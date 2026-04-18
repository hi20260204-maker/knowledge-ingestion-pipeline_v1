import pytest
from src.extractor.base import perform_extraction
from src.models import ExtractionResult


def mock_extractor_success(url):
    """성공하는 모의 추출 엔진."""
    return ExtractionResult(success=True, content="Mocked Success Content")


def mock_extractor_fail(url):
    """실패하는 모의 추출 엔진."""
    return ExtractionResult(success=False, error="Connection timeout")


def test_fallback_success_first_engine():
    """첫 번째 엔진이 성공하면 즉시 반환하는지 검증합니다."""
    engines = [mock_extractor_success, mock_extractor_fail]
    result = perform_extraction("http://example.com", engines)

    assert result.success is True
    assert result.content == "Mocked Success Content"


def test_fallback_success_second_engine():
    """첫 번째 엔진 실패 시 두 번째 엔진으로 폴백하는지 검증합니다."""
    engines = [mock_extractor_fail, mock_extractor_success]
    result = perform_extraction("http://example.com", engines)

    assert result.success is True
    assert result.content == "Mocked Success Content"


def test_fallback_all_fail():
    """모든 엔진 실패 시 에러 결과를 반환하는지 검증합니다."""
    engines = [mock_extractor_fail, mock_extractor_fail]
    result = perform_extraction("http://example.com", engines)

    assert result.success is False
    assert result.error is not None
