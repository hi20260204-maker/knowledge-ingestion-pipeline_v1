import hashlib
import re
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

def normalize_url(url: str) -> str:
    """
    도메인별 특화 규칙을 포함한 URL 표준화 작업을 수행합니다.
    트래킹 쿼리 파라미터 제외, Trailing Slash 제거, 프로토콜 통일 등을 처리합니다.
    """
    if not url: return ""
    
    # 1. 프로토콜 및 도메인 정규화 (Lowercasing domain, removing trailing slash)
    url = url.strip().rstrip('/')
    parsed = urlparse(url)
    
    # 2. 쿼리 파라미터 정제
    query_params = parse_qs(parsed.query)
    tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'ref', 'source', 'fbclid', 'rss_id'}
    query_params = {k: v for k, v in query_params.items() if k.lower() not in tracking_params and not k.startswith('utm_')}
    
    # 3. 도메인별 특화 규칙
    netloc = parsed.netloc.lower()
    if 'reddit.com' in netloc:
        query_params = {}
    elif 'news.ycombinator.com' in netloc:
        if 'id' not in query_params: query_params = {}
            
    clean_query = urlencode(query_params, doseq=True)
    
    # Fragment 및 불필요한 요소 제거한 Canonical URL 생성
    canonical_url = urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, clean_query, ''))
    
    return canonical_url

def normalize_content(html_content: str) -> str:
    """
    의미론적 본문 비교를 위해 콘텐츠를 정규화합니다.
    - HTML 태그 제거 및 소문자 변환
    - 내비게이션, 푸터, 광고 영역 등 노이즈 제거
    - 화이트스페이스 통합
    """
    if not html_content:
        return ""
        
    # 1. 태그 내 텍스트 추출 전 불필요한 블록 제거 (스크립트, 스타일, 내비게이션 등)
    # 실제 BS4를 쓰지 않는 경우 정규식으로 처리 (간결함 유지)
    html_content = re.sub(r'<(script|style|nav|footer|header)[^>]*>.*?</\1>', ' ', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. HTML 태그 제거
    text = re.sub(r'<[^>]+>', ' ', html_content)
    text = text.lower()
    
    # 3. 시간 및 소셜 기반 노이즈 제거 패턴 (광고/공유 버튼 등)
    noise_patterns = [
        r'\d+\s+(hours?|minutes?|days?|comments?)\s+ago',
        r'updated\s+\d+\s+hours?\s+ago',
        r'share\s+on\s+(facebook|twitter|linkedin|reddit)',
        r'©\s*\d{4}.*',
        r'all\s+rights\s+reserved',
        r'last\s+updated\s+at\s+[\d:]+'
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
    # 4. 화이트스페이스 정규화
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def generate_url_hash(url: str) -> str:
    """Generate a SHA-256 hash of a normalized URL."""
    canonical_url = normalize_url(url)
    return hashlib.sha256(canonical_url.encode('utf-8')).hexdigest()

def generate_content_hash(html_content: str) -> str:
    """
    정규화된 전체 본문을 기준으로 SHA-256 해시를 생성합니다.
    기존의 prefix(1000자) 방식에서 전체 본문 기반으로 변경하여 무결성을 강화했습니다.
    """
    normalized = normalize_content(html_content)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
