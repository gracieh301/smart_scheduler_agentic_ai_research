"""
Migration script to add structured_data column to syllabi table.
Run this once to update your existing database schema.
"""
import sqlite3
import os
from pathlib import Path

# Get database path
db_path = Path(__file__).parent.parent / "study_planner.db"

if not db_path.exists():
    print(f"Database not found at {db_path}. It will be created automatically on next run.")
    exit(0)

print(f"Updating database at {db_path}...")

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(syllabi)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if "structured_data" in columns:
        print("✓ Column 'structured_data' already exists. No migration needed.")
    else:
        # Add the structured_data column
        cursor.execute("ALTER TABLE syllabi ADD COLUMN structured_data TEXT")
        conn.commit()
        print("✓ Successfully added 'structured_data' column to syllabi table.")
    
    conn.close()
    print("Migration completed successfully!")
    
except Exception as e:
    print(f"Error during migration: {e}")
    exit(1)

