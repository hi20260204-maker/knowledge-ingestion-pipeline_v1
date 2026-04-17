import pytest
from src.extractor.fallback_engine import perform_extraction, ExtractionResult

def mock_extractor_success(url):
    return ExtractionResult(success=True, content="Mocked Success Content")

def mock_extractor_fail(url):
    return ExtractionResult(success=False, error="Connection timeout")

def test_fallback_success_first_engine():
    # Scenario: First engine (Crawl4AI equivalent) succeeds
    engines = [mock_extractor_success, mock_extractor_fail]
    result = perform_extraction("http://example.com", engines)
    
    assert result.success is True
    assert result.content == "Mocked Success Content"

def test_fallback_success_second_engine():
    # Scenario: First fails, second (Firecrawl equivalent) succeeds
    engines = [mock_extractor_fail, mock_extractor_success]
    result = perform_extraction("http://example.com", engines)
    
    assert result.success is True
    assert result.content == "Mocked Success Content"

def test_fallback_all_fail():
    # Scenario: All engines fail
    engines = [mock_extractor_fail, mock_extractor_fail]
    result = perform_extraction("http://example.com", engines)
    
    assert result.success is False
    assert result.error is not None
