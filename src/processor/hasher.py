import hashlib
import re
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

def normalize_url(url: str) -> str:
    """
    도메인별 특화 규칙을 포함한 URL 표준화 작업을 수행합니다.
    트래킹 쿼리 파라미터(utm_*, ref 등)를 제거합니다.
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # 1. 공통 트래킹 파라미터 제거
    tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'ref', 'source', 'fbclid'}
    query_params = {k: v for k, v in query_params.items() if k.lower() not in tracking_params and not k.startswith('utm_')}
    
    # 2. 도메인별 특화 규칙 (확장 가능한 구조)
    if 'reddit.com' in parsed.netloc:
        query_params = {} # Reddit index pages usually don't need query params for hashing
    elif 'news.ycombinator.com' in parsed.netloc:
        # Keep 'id' for items, but main page has no query
        if 'id' not in query_params:
            query_params = {}
            
    clean_query = urlencode(query_params, doseq=True)
    canonical_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, clean_query, ''))
    
    return canonical_url

def normalize_content(html_content: str) -> str:
    """
    중복 판정을 위해 콘텐츠를 정규화합니다.
    - HTML 태그 제거 및 소문자 변환 (해시용)
    - 연속된 공백/줄바꿈 통합
    - 시간 기반 노이즈 제거
    """
    if not html_content:
        return ""
        
    # 1. HTML 태그 제거
    text = re.sub(r'<[^>]+>', ' ', html_content)
    
    # 2. 소문자 변환 (해싱용 정규화)
    text = text.lower()
    
    # 3. 시간 관련 동적 노이즈 제거 패턴
    noise_patterns = [
        r'\d+\s+(hours?|minutes?|days?|comments?)\s+ago',
        r'updated\s+\d+\s+hours?\s+ago',
        r'just\s+now',
        r'last\s+updated\s+at\s+[\d:]+'
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, ' ', text)
        
    # 4. 화이트스페이스 정규화 (공백/줄바꿈 통합)
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
