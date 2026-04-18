import sqlite3
import os

DB_PATH = "knowledge.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"{DB_PATH} not found. Skipping migration.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if updated_at already exists
    cursor.execute("PRAGMA table_info(articles)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'updated_at' not in columns:
        try:
            # 1. Add column without non-constant default
            cursor.execute("ALTER TABLE articles ADD COLUMN updated_at DATETIME")
            # 2. Update existing rows with current timestamp
            cursor.execute("UPDATE articles SET updated_at = CURRENT_TIMESTAMP")
            conn.commit()
            print("Successfully added and initialized 'updated_at' column.")
        except Exception as e:
            print(f"Error adding column: {e}")
    else:
        print("'updated_at' column already exists.")
        
    conn.close()

if __name__ == "__main__":
    migrate()
