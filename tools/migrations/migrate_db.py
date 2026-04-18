import sqlite3
import os

DB_PATH = "knowledge.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"{DB_PATH} not found. Skipping migration.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Add status to articles
    try:
        cursor.execute("ALTER TABLE articles ADD COLUMN status TEXT DEFAULT 'NEW'")
        print("Added 'status' column to 'articles'.")
    except sqlite3.OperationalError:
        print("'status' column already exists in 'articles'.")
        
    # 2. Add parent_id to articles
    try:
        cursor.execute("ALTER TABLE articles ADD COLUMN parent_id INTEGER")
        print("Added 'parent_id' column to 'articles'.")
    except sqlite3.OperationalError:
        print("'parent_id' column already exists in 'articles'.")
        
    # 3. Add summary_version to summaries
    try:
        cursor.execute("ALTER TABLE summaries ADD COLUMN summary_version INTEGER DEFAULT 1")
        print("Added 'summary_version' column to 'summaries'.")
    except sqlite3.OperationalError:
        print("'summary_version' column already exists in 'summaries'.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
