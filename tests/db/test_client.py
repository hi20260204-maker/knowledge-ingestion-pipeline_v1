import pytest
import sqlite3
import os
from src.db.client import init_db

def test_init_db(tmp_path):
    db_path = tmp_path / "test.db"
    
    # We must construct an absolute path to the schema inside tests due to the relative path nature
    # Usually it's in src/db/schema.sql
    current_dir = os.path.dirname(__file__)
    schema_path = os.path.abspath(os.path.join(current_dir, '..', '..', 'src', 'db', 'schema.sql'))
    
    init_db(str(db_path), schema_path)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    
    assert "articles" in tables
    assert "summaries" in tables
    assert "pipeline_logs" in tables
    conn.close()
