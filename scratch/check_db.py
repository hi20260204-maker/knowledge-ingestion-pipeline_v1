import sqlite3
import os

DB_PATH = "knowledge.db"

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- Last 10 Articles ---")
    cursor.execute("SELECT source_id, title, published_at FROM articles ORDER BY id DESC LIMIT 10")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- Last 10 Summaries ---")
    cursor.execute("""
        SELECT a.source_id, s.importance_score, s.created_at 
        FROM summaries s 
        JOIN articles a ON s.article_id = a.id 
        ORDER BY s.id DESC LIMIT 10
    """)
    for row in cursor.fetchall():
        print(row)

    print("\n--- Last 10 Pipeline Logs ---")
    cursor.execute("SELECT target_url, stage, status, error_message FROM pipeline_logs ORDER BY id DESC LIMIT 10")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_db()
