import logging
from typing import Callable, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ExtractionResult(BaseModel):
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    used_engine: Optional[str] = None

# Type alias for our extractor functions
ExtractorFunc = Callable[[str], ExtractionResult]

def perform_extraction(url: str, engines: List[ExtractorFunc]) -> ExtractionResult:
    """
    Sequentially run through a list of extractor engines.
    Returns the result of the first successful extraction.
    If all fail, returns a final failure result.
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

# Stubs for the actual engines (to be connected to actual API clients later)
def engine_crawl4ai(url: str) -> ExtractionResult:
    # TODO: Implement actual Async WebCrawler logic when environment is stable
    return ExtractionResult(success=False, error="Not implemented")

def engine_firecrawl(url: str) -> ExtractionResult:
    # TODO: Implement FirecrawlApp scraper
    return ExtractionResult(success=False, error="Not implemented")

def engine_rss_fallback(url: str) -> ExtractionResult:
    # TODO: Fetch raw RSS feed summary
    return ExtractionResult(success=False, error="Not implemented")
