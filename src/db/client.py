import sqlite3
import json
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

def save_summary(db_path, article_id, summary_data):
    """
    Saves or updates intelligence data for an article.
    Updated for Phase 4: Supports global_score, personalized_score, and unified reason.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Unified 'reason' from Phase 4
    reason = summary_data.get('reason', summary_data.get('importance_reason', '일반 기술 소식'))
    g_score = summary_data.get('global_score', summary_data.get('importance_score', 50.0))
    p_score = summary_data.get('personalized_score', g_score)

    cursor.execute("""
        INSERT INTO summaries (
            article_id, summary_text, key_points, keywords, 
            importance_score, global_score, personalized_score, reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(article_id) DO UPDATE SET
            summary_text=excluded.summary_text,
            key_points=excluded.key_points,
            keywords=excluded.keywords,
            importance_score=excluded.importance_score,
            global_score=excluded.global_score,
            personalized_score=excluded.personalized_score,
            reason=excluded.reason
    """, (
        article_id, 
        summary_data['summary'], 
        json.dumps(summary_data['key_points']), 
        json.dumps(summary_data['keywords']),
        int(round(g_score/10.0)) if g_score > 10 else int(g_score),
        g_score,
        p_score,
        reason
    ))
    
    conn.commit()
    conn.close()

def get_daily_summary(db_path, date_str):
    """
    Retrieves all articles and their intelligence data for a specific day.
    Updated for Phase 4: Returns global_score, personalized_score, and unified reason.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, s.summary_text as summary, s.key_points, s.keywords, 
               s.global_score, s.personalized_score, s.reason
        FROM articles a
        JOIN summaries s ON a.id = s.article_id
        WHERE DATE(a.updated_at) = ?
        AND a.status IN ('NEW', 'UPDATED', 'SUMMARY_REUSED')
    """, (date_str,))
    
    rows = cursor.fetchall()
    items = []
    for row in rows:
        item = dict(row)
        # Robust JSON parsing for Phase 4
        try:
            item['key_points'] = json.loads(item['key_points']) if item.get('key_points') else []
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Invalid key_points format for article {item.get('id')}. Falling back to [].")
            item['key_points'] = []

        try:
            item['keywords'] = json.loads(item['keywords']) if item.get('keywords') else []
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Invalid keywords format for article {item.get('id')}. Falling back to [].")
            item['keywords'] = []

        # Support legacy 'url' field for distribution layers
        item['url'] = item.get('raw_url', item.get('canonical_url'))
        items.append(item)
        
    conn.close()
    return items
