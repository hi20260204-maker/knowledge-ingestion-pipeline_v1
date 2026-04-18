import sqlite3
import os

db_path = "knowledge.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    columns_to_add = [
        ("global_score", "REAL"),
        ("personalized_score", "REAL")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE summaries ADD COLUMN {col_name} {col_type};")
            print(f"Added column: {col_name}")
        except sqlite3.OperationalError:
            print(f"Column {col_name} already exists or error occurred.")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
