"""
Hacker News 추출 엔진.

Hacker News 인덱스 페이지를 파싱하여 포스트 목록을 추출합니다.
"""
import requests
from bs4 import BeautifulSoup
from src.models import ExtractedItem, ExtractionResult
from src.processor.hasher import normalize_url
from src.utils.logger import get_logger

logger = get_logger(__name__)


def engine_hn_listing(url: str) -> ExtractionResult:
    """Hacker News 인덱스 페이지를 파싱하여 포스트 목록을 추출합니다.

    BeautifulSoup을 사용하여 HN의 .titleline 구조를 파싱합니다.
    내부 HN 링크(item?id=)는 절대 경로로 변환됩니다.

    Args:
        url: Hacker News 페이지 URL

    Returns:
        ExtractionResult: 파싱된 포스트 목록
    """
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Knowledge-Bot/1.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        items = []

        # HN 구조: <span class="titleline"><a href="...">Title</a></span>
        links = soup.select(".titleline > a")

        for link in links:
            item_url = link.get('href', '')
            # 내부 HN 링크를 절대 경로로 변환
            if item_url.startswith('item?id='):
                item_url = f"https://news.ycombinator.com/{item_url}"

            item = ExtractedItem(
                title=link.get_text(),
                url=item_url,
                canonical_url=normalize_url(item_url),
                snippet="",
                source_name="Hacker News",
                source_type="hn_listing",
                fetch_mode="snippet"
            )
            items.append(item)

        if not items:
            return ExtractionResult(success=False, error="Failed to parse any items from HN")

        return ExtractionResult(success=True, items=items, used_engine="engine_hn_listing")
    except Exception as e:
        return ExtractionResult(success=False, error=str(e))
