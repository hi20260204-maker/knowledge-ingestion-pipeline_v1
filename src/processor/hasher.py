import hashlib
import re
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

def generate_url_hash(url: str) -> str:
    """
    Generate a SHA-256 hash of a URL after normalizing it.
    Removes tracking parameters such as utm_*.
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # Remove tracking parameters
    keys_to_remove = [k for k in query_params.keys() if k.startswith('utm_') or k == 'ref']
    for k in keys_to_remove:
        del query_params[k]
    
    clean_query = urlencode(query_params, doseq=True)
    canonical_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, clean_query, ''))
    
    return hashlib.sha256(canonical_url.encode('utf-8')).hexdigest()

def generate_content_hash(html_content: str) -> str:
    """
    Generate a SHA-256 hash of the content after aggressive normalization.
    Strips HTML tags, collapses whitespace, and extracts up to 1000 characters.
    """
    # 1. Strip HTML tags using regex (simplistic fallback, in reality BS4 is better)
    text = re.sub(r'<[^>]+>', ' ', html_content)
    
    # 2. Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 3. Truncate to first 1000 characters to prevent insignificant changes at the bottom affecting hash
    prefix = text[:1000]
    
    return hashlib.sha256(prefix.encode('utf-8')).hexdigest()
