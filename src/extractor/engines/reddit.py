"""
Reddit 추출 엔진.

Reddit 서브레딧 목록 페이지를 파싱하여 포스트 목록을 추출합니다.
"""
import requests
from bs4 import BeautifulSoup
from src.models import ExtractedItem, ExtractionResult
from src.processor.hasher import normalize_url
from src.utils.logger import get_logger

logger = get_logger(__name__)


def engine_reddit_listing(url: str) -> ExtractionResult:
    """Reddit 서브레딧 목록 페이지를 파싱하여 포스트 목록을 추출합니다.

    데스크톱 User-Agent를 사용하여 Reddit 차단을 우회합니다.
    댓글 링크(/comments/)를 기반으로 포스트를 식별하고,
    URL 기반 중복 제거를 수행합니다.

    Args:
        url: Reddit 서브레딧 URL

    Returns:
        ExtractionResult: 파싱된 포스트 목록
    """
    try:
        # 데스크톱 UA로 Reddit 차단 우회
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        items = []

        # 댓글 링크 패턴으로 포스트 식별
        links = soup.select('a[href*="/r/"][href*="/comments/"]')

        seen_urls = set()
        for link in links:
            item_url = link.get('href', '')
            # 상대 경로를 절대 경로로 변환
            if not item_url.startswith('http'):
                item_url = f"https://www.reddit.com{item_url}"

            # URL 기반 중복 제거 (제목/썸네일 등 여러 링크 존재)
            if item_url in seen_urls:
                continue
            seen_urls.add(item_url)

            title = link.get_text().strip()
            if not title or len(title) < 5:
                continue

            item = ExtractedItem(
                title=title,
                url=item_url,
                canonical_url=normalize_url(item_url),
                snippet="",
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
