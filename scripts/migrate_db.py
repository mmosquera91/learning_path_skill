#!/usr/bin/env python3
"""Migrate the Learning Path Generator SQLite database.

Usage:
    python3 migrate_db.py [--db PATH]

Compares schema_version in the DB with EXPECTED_VERSION and runs
ALTER TABLE statements as needed. Safe to run multiple times.
"""

import sqlite3
import os
import sys

DB_PATH = os.path.expanduser("~/.hermes/skills/tutor/learning.db")

EXPECTED_VERSION = 1

# Each key = version we're migrating TO
# Value = list of SQL statements to run
MIGRATIONS = {
    # Example for future versions:
    # 2: [
    #     "ALTER TABLE modules ADD COLUMN difficulty TEXT DEFAULT 'medium'",
    #     "ALTER TABLE daily_tasks ADD COLUMN time_spent_minutes INTEGER",
    #     "CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY, module_id INTEGER REFERENCES modules(id), tag TEXT)",
    # ],
}


def get_current_version(conn: sqlite3.Connection) -> int:
    """Get current schema version, or 0 if not initialized."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT version FROM schema_version")
        row = cursor.fetchone()
        return row[0] if row else 0
    except sqlite3.OperationalError:
        return 0


def migrate(db_path: str = DB_PATH):
    """Run migrations from current version to expected version."""
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}. Run init_db.py first.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")

    current = get_current_version(conn)

    if current == EXPECTED_VERSION:
        print(f"Already at schema v{current}. No migration needed.")
        conn.close()
        return

    if current > EXPECTED_VERSION:
        print(f"DB schema v{current} is newer than expected v{EXPECTED_VERSION}.")
        print("This might mean you're running an older version of the skill.")
        conn.close()
        return

    print(f"Migrating: v{current} -> v{EXPECTED_VERSION}")

    cursor = conn.cursor()

    for target_version in range(current + 1, EXPECTED_VERSION + 1):
        if target_version in MIGRATIONS:
            print(f"  Applying migration to v{target_version}...")
            for sql in MIGRATIONS[target_version]:
                try:
                    cursor.execute(sql)
                    print(f"    OK: {sql[:80]}...")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"    SKIP (already exists): {sql[:80]}...")
                    else:
                        print(f"    ERROR: {e}")
                        print(f"    SQL: {sql}")
                        conn.close()
                        sys.exit(1)
        else:
            print(f"  No migration steps for v{target_version} (schema change only)")

        # Update version
        if current == 0:
            cursor.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (target_version,),
            )
        else:
            cursor.execute(
                "UPDATE schema_version SET version = ?", (target_version,)
            )

        conn.commit()
        current = target_version

    print(f"Migration complete. Now at v{current}.")
    conn.close()


if __name__ == "__main__":
    path = DB_PATH
    if "--db" in sys.argv:
        idx = sys.argv.index("--db")
        if idx + 1 < len(sys.argv):
            path = sys.argv[idx + 1]
    migrate(path)
