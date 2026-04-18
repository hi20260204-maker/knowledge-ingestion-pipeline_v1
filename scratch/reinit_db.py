import sqlite3
import os

db_path = "knowledge.db"
schema_path = "src/db/schema.sql"

def reinit():
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing {db_path}")

    conn = sqlite3.connect(db_path)
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_script = f.read()
        conn.executescript(schema_script)
    
    conn.commit()
    conn.close()
    print("Clean Knowledge DB with Phase 4 Constraints (UNIQUE, etc.) Initialized Successfully.")

if __name__ == "__main__":
    reinit()
