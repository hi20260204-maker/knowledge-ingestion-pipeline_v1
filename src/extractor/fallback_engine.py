import logging
import requests
from typing import Callable, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ExtractionResult(BaseModel):
    success: bool
    content: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
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

# ACTUAL IMPLEMENTATIONS

def engine_crawl4ai(url: str) -> ExtractionResult:
    # TODO: Implement actual Async WebCrawler logic when environment is stable
    return ExtractionResult(success=False, error="Crawl4AI not configured for synchronous test")

def engine_firecrawl(url: str) -> ExtractionResult:
    # TODO: Implement FirecrawlApp scraper
    return ExtractionResult(success=False, error="Firecrawl not configured")

def engine_rss_fallback(url: str) -> ExtractionResult:
    """
    Fetches raw content from a URL via requests.
    Used for RSS feeds or simple static pages.
    """
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Knowledge-Ingestion-Bot/1.0"})
        response.raise_for_status()
        
        # Simple proof of concept: return the raw text (up to 10k chars)
        content = response.text[:10000]
        
        return ExtractionResult(
            success=True, 
            content=content,
            title=f"Extracted from {url}",
            url=url
        )
    except Exception as e:
        return ExtractionResult(success=False, error=str(e))
