"""
RSS 기반 추출 엔진.

RSS 피드를 파싱하여 개별 기사 아이템으로 변환하는 엔진과
단순 HTTP 폴백 엔진을 제공합니다.
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from src.models import ExtractedItem, ExtractionResult
from src.processor.hasher import normalize_url
from src.utils.logger import get_logger

logger = get_logger(__name__)


def engine_rss_itemized(url: str) -> ExtractionResult:
    """RSS 피드를 파싱하여 개별 ExtractedItem 목록으로 변환합니다.

    feedparser를 사용하여 RSS/Atom 피드를 파싱하고,
    각 엔트리를 ExtractedItem으로 변환합니다.
    HTML 태그는 BeautifulSoup으로 제거됩니다.

    Args:
        url: RSS 피드 URL

    Returns:
        ExtractionResult: 파싱된 아이템 목록을 포함한 결과
    """
    try:
        d = feedparser.parse(url)

        if d.bozo:
            logger.warning(f"Feedparser flagged potential issue with {url}: {d.bozo_exception}")

        if not d.entries:
            return ExtractionResult(success=False, error="No entries found in feed")

        items = []
        for entry in d.entries:
            # 엔트리에서 요약/설명 추출
            snippet = entry.get('summary', entry.get('description', ''))

            # HTML 태그 제거 (BeautifulSoup 사용)
            try:
                soup = BeautifulSoup(snippet, "html.parser")
                snippet = soup.get_text(separator=' ', strip=True)[:1000]
            except Exception:
                snippet = snippet[:1000]

            item = ExtractedItem(
                title=entry.get('title', 'Untitled Result'),
                url=entry.get('link', ''),
                canonical_url=normalize_url(entry.get('link', '')),
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


def engine_rss_fallback(url: str) -> ExtractionResult:
    """단순 HTTP 요청으로 원본 콘텐츠를 가져오는 최후 보루 엔진.

    RSS/목록형이 아닌 단순 정적 페이지를 위한 폴백입니다.
    최대 10,000자만 가져옵니다.

    Args:
        url: 대상 URL

    Returns:
        ExtractionResult: 원본 콘텐츠를 content 필드에 담은 결과
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
