import logging
import requests
from typing import Callable, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ExtractedItem(BaseModel):
    """Represents a single article or post extracted from a source."""
    title: str
    url: str
    canonical_url: Optional[str] = None
    snippet: Optional[str] = None
    published_at: Optional[str] = None
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    fetch_mode: str = "snippet" # "snippet" or "full"
    raw_content: Optional[str] = None

class ExtractionResult(BaseModel):
    """Results from the extraction engine, now supporting multiple items."""
    success: bool
    items: List[ExtractedItem] = []
    # Legacy fields for single-page compatibility
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

import feedparser
from bs4 import BeautifulSoup
from src.processor.hasher import normalize_url

# ACTUAL IMPLEMENTATIONS

def engine_rss_itemized(url: str) -> ExtractionResult:
    """
    Parses RSS feeds into individual ExtractedItem objects using feedparser.
    """
    try:
        # User-Agent header handled by feedparser is sometimes basic, 
        # but we can pass a response or just the URL
        d = feedparser.parse(url)
        
        if d.bozo:
            logger.warning(f"Feedparser flagged potential issue with {url}: {d.bozo_exception}")
            
        if not d.entries:
            return ExtractionResult(success=False, error="No entries found in feed")
            
        items = []
        for entry in d.entries:
            # Extract content/snippet
            snippet = entry.get('summary', entry.get('description', ''))
            
            # Clean HTML from snippet if BS is available
            try:
                soup = BeautifulSoup(snippet, "html.parser")
                snippet = soup.get_text(separator=' ', strip=True)[:1000]
            except Exception:
                snippet = snippet[:1000]
            
            item = ExtractedItem(
                title=entry.get('title', 'Untitled Result'),
                url=entry.get('link', ''),
                canonical_url=normalize_url(entry.get('link', '')), # Best effort
                snippet=snippet,
                published_at=entry.get('published', entry.get('updated', None)),
                source_name=d.feed.get('title', 'RSS Feed'),
                source_type="rss_item",
                fetch_mode="snippet"
            )
            items.append(item)
            
        return ExtractionResult(
            success=True,
            items=items,
            used_engine="engine_rss_itemized"
        )
    except Exception as e:
        return ExtractionResult(success=False, error=str(e))

def engine_hn_listing(url: str) -> ExtractionResult:
    """
    Lightweight parser for Hacker News index page using BeautifulSoup.
    """
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Knowledge-Bot/1.0"})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        items = []
        
        # HN structure: <span class="titleline"><a href="...">Title</a></span>
        links = soup.select(".titleline > a")
        
        for link in links:
            item_url = link.get('href', '')
            # If internal HN link, make it absolute
            if item_url.startswith('item?id='):
                item_url = f"https://news.ycombinator.com/{item_url}"
                
            item = ExtractedItem(
                title=link.get_text(),
                url=item_url,
                canonical_url=normalize_url(item_url),
                snippet="", # HN index doesn't provide snippets
                source_name="Hacker News",
                source_type="hn_listing",
                fetch_mode="snippet"
            )
            items.append(item)
            
        if not items:
            return ExtractionResult(success=False, error="Failed to parse any items from HN")
            
        return ExtractionResult(success=True, items=items, used_engine="engine_hn_listing")
    except Exception as e:
        # Fallback will be handled by perform_extraction
        return ExtractionResult(success=False, error=str(e))

def engine_reddit_listing(url: str) -> ExtractionResult:
    """
    Experimental lightweight parser for Reddit subreddit listings.
    Note: Reddit often blocks simple scrapers, so this is a best-effort.
    """
    try:
        # High-quality desktop UA is often required for Reddit
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        items = []
        
        # Reddit structure varies by version, but common patterns:
        # Look for post links (shredded-post title attribute or specific link classes)
        # Using a broad approach: find all a tags that look like post links
        links = soup.select('a[href*="/r/"][href*="/comments/"]')
        
        seen_urls = set()
        for link in links:
            item_url = link.get('href', '')
            if not item_url.startswith('http'):
                item_url = f"https://www.reddit.com{item_url}"
                
            # Deduplicate multiple links to same post (e.g. title and thumbnail)
            if item_url in seen_urls: continue
            seen_urls.add(item_url)
            
            title = link.get_text().strip()
            if not title or len(title) < 5: continue
                
            item = ExtractedItem(
                title=title,
                url=item_url,
                canonical_url=normalize_url(item_url),
                snippet="", # Reddit index snippets are hard to parse without full CSS
                source_name=f"Reddit ({url.split('/r/')[-1]})",
                source_type="reddit_listing",
                fetch_mode="snippet"
            )
            items.append(item)
            
        if not items:
            return ExtractionResult(success=False, error="Failed to find any Reddit posts in HTML")
            
        return ExtractionResult(success=True, items=items, used_engine="engine_reddit_listing")
    except Exception as e:
        return ExtractionResult(success=False, error=str(e))

def engine_rss_fallback(url: str) -> ExtractionResult:
    """
    Legacy fallback: Fetches raw content from a URL via requests.
    Used for simple static pages that aren't listing pages.
    """
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Knowledge-Ingestion-Bot/1.0"})
        response.raise_for_status()
        content = response.text[:10000]
        
        return ExtractionResult(
            success=True, 
            content=content,
            title=f"Extracted from {url}",
            url=url,
            used_engine="engine_rss_fallback"
        )
    except Exception as e:
        return ExtractionResult(success=False, error=str(e))
