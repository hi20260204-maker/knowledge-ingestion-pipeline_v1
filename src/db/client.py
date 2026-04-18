"""
SQLite 데이터베이스 클라이언트.

articles, summaries 테이블에 대한 CRUD 작업과
Context Manager 기반 안전한 연결 관리를 제공합니다.
"""
import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

CURRENT_SUMMARY_VERSION = 1


@contextmanager
def get_connection(db_path: str):
    """SQLite 데이터베이스 연결을 안전하게 관리하는 Context Manager.

    트랜잭션 자동 커밋/롤백 및 연결 종료를 보장합니다.
    예외 발생 시 자동으로 롤백하여 데이터 일관성을 유지합니다.

    Args:
        db_path: SQLite 데이터베이스 파일 경로

    Yields:
        sqlite3.Connection: 활성 데이터베이스 연결

    Example:
        with get_connection("knowledge.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
    """
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str, schema_path: str):
    """SQLite 데이터베이스를 스키마 파일로 초기화합니다.

    Args:
        db_path: 생성할 데이터베이스 파일 경로
        schema_path: SQL 스키마 파일 경로
    """
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_script = f.read()

    with get_connection(db_path) as conn:
        conn.executescript(schema_script)


def check_duplicate(db_path: str, url_hash: str, content_hash: str) -> bool:
    """동일 URL + 동일 Content의 정확한 중복 여부를 확인합니다.

    URL 해시와 콘텐츠 해시가 모두 일치하는 레코드가 있으면 중복으로 판단합니다.
    같은 URL이라도 콘텐츠가 변경되면 중복이 아닙니다 (UPDATED 판정 가능).

    Args:
        db_path: 데이터베이스 파일 경로
        url_hash: 정규화된 URL의 SHA-256 해시
        content_hash: 정규화된 콘텐츠의 SHA-256 해시

    Returns:
        중복 존재 여부
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM articles WHERE url_hash = ? AND content_hash = ?",
            (url_hash, content_hash)
        )
        return cursor.fetchone() is not None


def find_latest_article_id(db_path: str, url_hash: str) -> Optional[int]:
    """특정 URL의 가장 최근 아티클 ID를 조회합니다 (리니지 추적용).

    같은 URL에서 콘텐츠가 변경된 경우, 이전 버전의 ID를 찾아
    parent_id로 연결하여 변경 이력을 추적합니다.

    Args:
        db_path: 데이터베이스 파일 경로
        url_hash: 정규화된 URL의 SHA-256 해시

    Returns:
        가장 최근 아티클 ID, 없으면 None
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM articles WHERE url_hash = ? ORDER BY id DESC LIMIT 1", (url_hash,))
        result = cursor.fetchone()
        return result[0] if result else None


def find_reusable_summary(db_path: str, content_hash: str, version: int = CURRENT_SUMMARY_VERSION) -> Optional[Dict[str, Any]]:
    """동일 콘텐츠 해시에 대한 기존 요약을 조회합니다 (재사용용).

    같은 콘텐츠로 이미 요약이 생성된 경우, LLM 호출 비용을 절약하기 위해
    기존 요약을 재사용합니다.
    Phase 4 필드(global_score, personalized_score, reason)도 포함합니다.

    Args:
        db_path: 데이터베이스 파일 경로
        content_hash: 콘텐츠 해시
        version: 요약 버전 (호환성 보장용)

    Returns:
        요약 데이터 딕셔너리, 없으면 None
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.importance_score, s.summary_text, s.key_points, s.keywords,
                   s.global_score, s.personalized_score, s.reason
            FROM summaries s
            JOIN articles a ON s.article_id = a.id
            WHERE a.content_hash = ? AND s.summary_version = ?
            ORDER BY s.id DESC LIMIT 1
        """, (content_hash, version))
        result = cursor.fetchone()

    if result:
        return {
            'importance_score': result[0],
            'summary': result[1],
            'key_points': result[2].split(", ") if result[2] else [],
            'keywords': result[3].split(", ") if result[3] else [],
            'global_score': result[4],
            'personalized_score': result[5],
            'reason': result[6]
        }
    return None


def save_article(db_path: str, article_data: Dict[str, Any]) -> int:
    """아티클 원본 데이터를 DB에 저장합니다.

    상태(NEW/UPDATED/LOW_QUALITY), 리니지(parent_id), 타임스탬프를 포함하여
    articles 테이블에 레코드를 삽입합니다.

    Args:
        db_path: 데이터베이스 파일 경로
        article_data: 아티클 데이터 딕셔너리
            필수 키: source_id, raw_url, canonical_url, title, url_hash,
                     content_hash, raw_content
            선택 키: published_at, status, parent_id

    Returns:
        생성된 아티클의 ID
    """
    now = datetime.now().isoformat()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
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
        return cursor.lastrowid


def save_summary(db_path: str, article_id: int, summary_data: Dict[str, Any]):
    """아티클의 요약 및 스코어링 데이터를 저장합니다.

    Phase 4 Dual-Score 체계(global_score, personalized_score)를 지원합니다.
    레거시 importance_score는 global_score에서 1-10 스케일로 변환하여 호환성을 유지합니다.
    기존 레코드가 있으면 UPSERT로 업데이트합니다.

    Args:
        db_path: 데이터베이스 파일 경로
        article_id: 대상 아티클 ID
        summary_data: 요약 데이터 딕셔너리
            필수 키: summary, key_points, keywords
            선택 키: global_score, personalized_score, reason
    """
    # Phase 4 / 레거시 필드 호환 처리
    reason = summary_data.get('reason', summary_data.get('importance_reason', '일반 기술 소식'))
    g_score = summary_data.get('global_score', summary_data.get('importance_score', 50.0))
    p_score = summary_data.get('personalized_score', g_score)

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
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
            int(round(g_score / 10.0)) if g_score > 10 else int(g_score),
            g_score,
            p_score,
            reason
        ))


def get_daily_summary(db_path: str, date_str: str) -> List[Dict[str, Any]]:
    """특정 날짜의 모든 아티클 + 요약 데이터를 조회합니다.

    Phase 4 Dual-Score 필드를 포함하여 반환합니다.
    JSON 필드(key_points, keywords)의 파싱 오류를 안전하게 처리합니다.

    Args:
        db_path: 데이터베이스 파일 경로
        date_str: 조회 날짜 (YYYY-MM-DD 형식)

    Returns:
        아티클 + 요약 데이터 딕셔너리 목록
    """
    with get_connection(db_path) as conn:
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
        # JSON 필드 안전 파싱
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

        # 레거시 'url' 필드 호환 (distribution 레이어용)
        item['url'] = item.get('raw_url', item.get('canonical_url'))
        items.append(item)

    return items
