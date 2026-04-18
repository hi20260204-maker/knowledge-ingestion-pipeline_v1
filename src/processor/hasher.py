"""
URL 및 콘텐츠 해싱 모듈.

URL 정규화, 콘텐츠 정규화, SHA-256 해시 생성 기능을 제공합니다.
중복 검사의 핵심 로직으로, 데이터 무결성의 기반이 됩니다.
"""
import hashlib
import re
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

# URL 정규화 시 제거할 트래킹 쿼리 파라미터 목록
TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term',
    'utm_content', 'ref', 'source', 'fbclid', 'rss_id'
}

# 콘텐츠 정규화 시 제거할 노이즈 패턴 (시간/소셜/저작권 등)
NOISE_PATTERNS = [
    r'\d+\s+(hours?|minutes?|days?|comments?)\s+ago',
    r'updated\s+\d+\s+hours?\s+ago',
    r'share\s+on\s+(facebook|twitter|linkedin|reddit)',
    r'©\s*\d{4}.*',
    r'all\s+rights\s+reserved',
    r'last\s+updated\s+at\s+[\d:]+'
]


def normalize_url(url: str) -> str:
    """도메인별 특화 규칙을 포함한 URL 정규화를 수행합니다.

    처리 과정:
    1. 프로토콜/도메인 소문자 변환 및 Trailing Slash 제거
    2. 트래킹 쿼리 파라미터 제거 (utm_*, ref, fbclid 등)
    3. 도메인별 특화 규칙 적용 (Reddit: 모든 쿼리 제거, HN: id만 유지)
    4. Fragment(#) 제거

    Args:
        url: 정규화할 원본 URL

    Returns:
        정규화된 Canonical URL (빈 문자열이면 빈 문자열 반환)
    """
    if not url:
        return ""

    # 1. 프로토콜 및 도메인 정규화
    url = url.strip().rstrip('/')
    parsed = urlparse(url)

    # 2. 쿼리 파라미터 정제
    query_params = parse_qs(parsed.query)
    query_params = {
        k: v for k, v in query_params.items()
        if k.lower() not in TRACKING_PARAMS and not k.startswith('utm_')
    }

    # 3. 도메인별 특화 규칙
    netloc = parsed.netloc.lower()
    if 'reddit.com' in netloc:
        query_params = {}
    elif 'news.ycombinator.com' in netloc:
        if 'id' not in query_params:
            query_params = {}

    clean_query = urlencode(query_params, doseq=True)

    # 4. Fragment 제거 후 Canonical URL 생성
    canonical_url = urlunparse((
        parsed.scheme, netloc, parsed.path,
        parsed.params, clean_query, ''
    ))

    return canonical_url


def normalize_content(html_content: str) -> str:
    """의미론적 비교를 위해 HTML 콘텐츠를 정규화합니다.

    처리 과정:
    1. 스크립트, 스타일, 내비게이션, 푸터, 헤더 블록 제거
    2. HTML 태그 제거 및 소문자 변환
    3. 시간/소셜 기반 노이즈 패턴 제거 (광고, 공유 버튼, 저작권 등)
    4. 화이트스페이스 정규화

    Args:
        html_content: 정규화할 HTML 콘텐츠

    Returns:
        정규화된 텍스트 (빈 입력이면 빈 문자열 반환)
    """
    if not html_content:
        return ""

    # 1. 불필요한 블록 제거 (스크립트, 스타일, 내비게이션 등)
    html_content = re.sub(
        r'<(script|style|nav|footer|header)[^>]*>.*?</\1>',
        ' ', html_content, flags=re.DOTALL | re.IGNORECASE
    )

    # 2. HTML 태그 제거 및 소문자 변환
    text = re.sub(r'<[^>]+>', ' ', html_content)
    text = text.lower()

    # 3. 시간/소셜 노이즈 제거
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)

    # 4. 화이트스페이스 정규화
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def generate_url_hash(url: str) -> str:
    """정규화된 URL의 SHA-256 해시를 생성합니다.

    URL을 먼저 정규화한 후 해시합니다.
    동일한 페이지를 가리키는 다른 URL 표기가 같은 해시를 갖도록 보장합니다.

    Args:
        url: 해싱할 URL

    Returns:
        URL의 SHA-256 해시 (16진수 문자열)
    """
    canonical_url = normalize_url(url)
    return hashlib.sha256(canonical_url.encode('utf-8')).hexdigest()


def generate_content_hash(html_content: str) -> str:
    """정규화된 전체 본문의 SHA-256 해시를 생성합니다.

    콘텐츠를 먼저 정규화(노이즈 제거, 소문자 변환)한 후 해시합니다.
    전체 본문 기반으로 무결성을 보장합니다.

    Args:
        html_content: 해싱할 HTML 콘텐츠

    Returns:
        콘텐츠의 SHA-256 해시 (16진수 문자열)
    """
    normalized = normalize_content(html_content)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
