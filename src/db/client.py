import sqlite3
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

def init_db(db_path: str, schema_path: str):
    """Initialize the SQLite database with the given schema script."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_script = f.read()
    
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_script)
    conn.commit()
    conn.close()

def check_duplicate(db_path: str, url_hash: str, content_hash: str) -> bool:
    """Check if an article already exists by URL hash or content hash."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM articles WHERE url_hash = ? OR content_hash = ?", 
        (url_hash, content_hash)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_article(db_path: str, article_data: dict) -> int:
    """Save raw article data and return the inserted row ID."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO articles (source_id, raw_url, canonical_url, title, url_hash, content_hash, raw_content, published_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        article_data['source_id'], article_data['raw_url'], article_data['canonical_url'],
        article_data['title'], article_data['url_hash'], article_data['content_hash'],
        article_data['raw_content'], datetime.now().isoformat()
    ))
    
    article_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return article_id

def save_summary(db_path: str, article_id: int, summary_data: dict):
    """Save LLM summary results linked to an article."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO summaries (article_id, importance_score, summary_text, key_points, keywords, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        article_id, summary_data['importance_score'], summary_data['summary'],
        ", ".join(summary_data['key_points']), ", ".join(summary_data['keywords']),
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()
