import sqlite3
import os

def main():
    db_path = "database.db"
    if not os.path.exists(db_path):
        print(f"Database file '{db_path}' not found.")
        return
        
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check rows count in daily_challenges
        cursor.execute("SELECT COUNT(*) FROM daily_challenges")
        count = cursor.fetchone()[0]
        print(f"Found {count} existing daily challenge records.")
        
        if count > 0:
            cursor.execute("DELETE FROM daily_challenges")
            conn.commit()
            print("Successfully cleared all daily challenge records from the database!")
            
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
