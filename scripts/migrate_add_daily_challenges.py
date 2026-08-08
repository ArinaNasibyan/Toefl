"""Add daily_challenges table to database."""

import asyncio
import sqlite3
from pathlib import Path


async def migrate_database() -> None:
    """Add daily_challenges table to existing database."""
    db_path = Path("database.db")

    if not db_path.exists():
        print("Database file not found. No migration needed.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table already exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='daily_challenges'"
        )
        if cursor.fetchone():
            print("Table 'daily_challenges' already exists. No migration needed.")
            return

        # Create the daily_challenges table
        print("Creating 'daily_challenges' table...")
        cursor.execute("""
            CREATE TABLE daily_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                challenge_date DATE NOT NULL,
                challenge_type VARCHAR(50) NOT NULL,
                content_id VARCHAR(100) NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0,
                score INTEGER,
                total_questions INTEGER,
                completed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Create indexes
        cursor.execute(
            "CREATE INDEX ix_daily_challenges_user_id ON daily_challenges(user_id)"
        )
        cursor.execute(
            "CREATE INDEX ix_daily_challenges_challenge_date ON daily_challenges(challenge_date)"
        )

        conn.commit()
        print("Migration completed successfully!")
        print("   - Created 'daily_challenges' table")
        print("   - Added indexes for user_id and challenge_date")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate_database())
