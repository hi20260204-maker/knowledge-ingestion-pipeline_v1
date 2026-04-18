import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

CURRENT_SUMMARY_VERSION = 1

def init_db(db_path: str, schema_path: str):
    """Initialize the SQLite database with the given schema script."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_script = f.read()
    
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_script)
    conn.commit()
    conn.close()

def check_duplicate(db_path: str, url_hash: str, content_hash: str) -> bool:
    """
    Check if an exact duplicate exists (same URL AND same Content).
    Combined with lineage, this allows the same URL to be updated if content changes.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM articles WHERE url_hash = ? AND content_hash = ?", 
        (url_hash, content_hash)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

def find_latest_article_id(db_path: str, url_hash: str) -> Optional[int]:
    """Find the most recent article ID for a given URL (for lineage tracking)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM articles WHERE url_hash = ? ORDER BY id DESC LIMIT 1", (url_hash,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def find_reusable_summary(db_path: str, content_hash: str, version: int = CURRENT_SUMMARY_VERSION) -> Optional[Dict[str, Any]]:
    """Find an existing summary for the same content and version."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.importance_score, s.summary_text, s.key_points, s.keywords
        FROM summaries s
        JOIN articles a ON s.article_id = a.id
        WHERE a.content_hash = ? AND s.summary_version = ?
        ORDER BY s.id DESC LIMIT 1
    """, (content_hash, version))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'importance_score': result[0],
            'summary': result[1],
            'key_points': result[2].split(", ") if result[2] else [],
            'keywords': result[3].split(", ") if result[3] else []
        }
    return None

def save_article(db_path: str, article_data: Dict[str, Any]) -> int:
    """Save raw article data with status, lineage, and explicit updated_at."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO articles (
            source_id, raw_url, canonical_url, title, url_hash, 
            content_hash, raw_content, published_at, status, parent_id, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        article_data['source_id'], article_data['raw_url'], article_data['canonical_url'],
        article_data['title'], article_data['url_hash'], article_data['content_hash'],
        article_data['raw_content'], article_data.get('published_at', now),
        article_data.get('status', 'NEW'), article_data.get('parent_id'),
        now
    ))
    
    article_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return article_id

def save_summary(db_path: str, article_id: int, summary_data: Dict[str, Any], version: int = CURRENT_SUMMARY_VERSION):
    """Save LLM summary results linked to an article with versioning."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO summaries (article_id, importance_score, importance_reason, summary_text, key_points, keywords, summary_version, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        article_id, summary_data['importance_score'], summary_data.get('importance_reason'),
        summary_data['summary'], ", ".join(summary_data['key_points']), 
        ", ".join(summary_data['keywords']), version, datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()

def get_daily_summary(db_path: str, date_str: str, version: int = CURRENT_SUMMARY_VERSION) -> List[Dict[str, Any]]:
    """
    Get the latest snapshot for a specific date.
    - One record per canonical_url (latest updated_at)
    - Valid summary with matching version
    - Specific statuses only
    """
    conn = sqlite3.connect(db_path)
    # Allows accessing rows by column name
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Use MAX(id) as the ultimate tie-breaker for latest record per canonical_url
    query = """
        SELECT a.id, a.canonical_url, a.title, a.content_hash, a.status, a.raw_url as url,
               s.importance_score as score, s.importance_reason as reason, s.summary_text as summary, s.key_points, s.keywords
        FROM articles a
        JOIN (
            SELECT canonical_url, MAX(id) as latest_id
            FROM articles
            WHERE date(updated_at) = ?
            AND status IN ('NEW', 'UPDATED', 'SUMMARY_REUSED')
            GROUP BY canonical_url
        ) latest ON a.id = latest.latest_id
        JOIN summaries s ON a.id = s.article_id
        WHERE s.summary_version = ?
        ORDER BY s.importance_score DESC
    """
    
    cursor.execute(query, (date_str, version))
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        item = dict(row)
        # Convert comma-separated strings back to lists
        if item.get('key_points'):
            item['key_points'] = item['key_points'].split(", ")
        if item.get('keywords'):
            item['keywords'] = item['keywords'].split(", ")
        results.append(item)
        
    conn.close()
    return results
