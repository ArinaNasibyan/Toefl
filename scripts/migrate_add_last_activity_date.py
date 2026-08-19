"""Add last_activity_date column to users table."""

import asyncio
import sqlite3
from pathlib import Path


async def migrate_database() -> None:
    """Add last_activity_date column to existing users table."""
    db_path = Path("database.db")

    if not db_path.exists():
        print("Database file not found. No migration needed.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        if "last_activity_date" in columns:
            print("✅ Column 'last_activity_date' already exists. No migration needed.")
            return

        # Add the new column
        print("Adding 'last_activity_date' column to users table...")
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN last_activity_date DATE
        """)

        conn.commit()
        print("✅ Migration completed successfully!")
        print("   - Added 'last_activity_date' column (nullable DATE)")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate_database())
