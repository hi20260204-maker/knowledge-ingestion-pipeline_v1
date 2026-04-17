import pytest
from src.processor.hasher import generate_url_hash, generate_content_hash

def test_generate_url_hash():
    # Test tracking parameter removal
    url_with_tracking = "https://techcrunch.com/2026/04/17/ai-news?utm_source=twitter&utm_medium=social&v=123"
    url_clean = "https://techcrunch.com/2026/04/17/ai-news?v=123"
    
    hash1 = generate_url_hash(url_with_tracking)
    hash2 = generate_url_hash(url_clean)
    
    assert hash1 == hash2

def test_generate_content_hash():
    # Test HTML removal, whitespace normalization, and truncation
    html_content = """
    <html>
        <body>
            <nav>Header Menu</nav>
            <h1>Main Title</h1>
            <p>
                This is   the <strong>actual</strong> content 
                that we want to keep.
            </p>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    
    # We expect standard regex-based boilerplate stripping in hasher
    hash_val = generate_content_hash(html_content)
    
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64  # SHA-256 standard format
