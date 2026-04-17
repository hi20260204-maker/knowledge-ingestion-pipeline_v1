import sqlite3

def init_db(db_path: str, schema_path: str):
    """Initialize the SQLite database with the given schema script."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_script = f.read()
    
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_script)
    conn.commit()
    conn.close()
