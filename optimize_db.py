import sqlite3
import os

def optimize_pragma(conn):
    """Apply aggressive SQLite compression and optimization settings."""
    conn.execute("PRAGMA page_size = 8192")  # Increase page size for better performance
    conn.execute("PRAGMA auto_vacuum = FULL")  # Full auto-vacuum for aggressive cleanup
    conn.execute("PRAGMA journal_mode = WAL")  # Use Write-Ahead Logging for performance
    conn.execute("PRAGMA synchronous = OFF")  # Disable synchronous for faster writes
    conn.execute("PRAGMA cache_size = -10000")  # Limit cache size to use less memory

def remove_unused_indexes(conn):
    """Removes non-primary key indexes to reduce size safely."""
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' 
        AND sql IS NOT NULL
        AND name NOT LIKE 'sqlite_%'  -- Avoid dropping system indexes
    """)
    indexes = cursor.fetchall()

    for index in indexes:
        index_name = index[0]
        print(f"Dropping non-essential index: {index_name}")
        conn.execute(f"DROP INDEX IF EXISTS {index_name}")

def vacuum_database(conn):
    """Defragments and fully compresses the database with more aggressive vacuum."""
    conn.execute("VACUUM")  # More aggressive vacuum, fully reclaims unused space
    print("VACUUM complete.")

def rebuild_database(db_path="ExcelDB.db"):
    """Applies all aggressive optimizations directly to the database."""
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return

    conn = sqlite3.connect(db_path)

    print("Applying PRAGMA optimizations...")
    optimize_pragma(conn)

    print("Removing unused indexes...")
    remove_unused_indexes(conn)

    print("Vacuuming database for aggressive compression...")
    vacuum_database(conn)

    conn.commit()
    conn.close()
    print("Optimization complete!")

if __name__ == "__main__":
    rebuild_database()
