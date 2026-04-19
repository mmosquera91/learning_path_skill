#!/usr/bin/env python3
"""Migrate the Learning Path Generator SQLite database.

Usage:
    python3 migrate_db.py [--db PATH]
    python3 migrate_db.py --down [--db PATH]

Compares schema_version in the DB with EXPECTED_VERSION and runs
ALTER TABLE statements as needed. Safe to run multiple times.
Supports down-migration to revert to previous schema version.
"""

import sqlite3
import shutil
import os
import sys

DB_PATH = os.path.expanduser("~/.hermes/skills/tutor/learning.db")

EXPECTED_VERSION = 3

# Each key = version we're migrating TO
# Value = list of SQL statements to run
MIGRATIONS = {
    2: [
        "ALTER TABLE modules ADD COLUMN score REAL DEFAULT 0",
        "ALTER TABLE modules ADD COLUMN next_review_date TEXT",
        "ALTER TABLE daily_tasks ADD COLUMN response_window_end TEXT",
        "ALTER TABLE daily_tasks ADD COLUMN feedback TEXT",
        "INSERT OR IGNORE INTO config (key, value) VALUES ('last_task_date', '')",
        "INSERT OR IGNORE INTO config (key, value) VALUES ('daily_count', '0')",
        "INSERT OR IGNORE INTO config (key, value) VALUES ('weekly_count', '0')",
        "INSERT OR IGNORE INTO config (key, value) VALUES ('response_window_end', '')",
    ],
}

# Reverse migrations: recreate tables without new columns
REVERSE_MIGRATIONS = {
    2: [
        "CREATE TABLE modules_backup AS SELECT id, path_id, title, description, module_order, status, score_avg, times_repeated, started, completed FROM modules",
        "DROP TABLE modules",
        "ALTER TABLE modules_backup RENAME TO modules",
        "CREATE INDEX IF NOT EXISTS idx_modules_path_id ON modules(path_id)",
        "CREATE TABLE daily_tasks_backup AS SELECT id, module_id, date, content, response, score, feedback, skipped, awaiting_response FROM daily_tasks",
        "DROP TABLE daily_tasks",
        "ALTER TABLE daily_tasks_backup RENAME TO daily_tasks",
        "CREATE INDEX IF NOT EXISTS idx_daily_tasks_module_id ON daily_tasks(module_id)",
        "DELETE FROM config WHERE key IN ('last_task_date', 'daily_count', 'weekly_count', 'response_window_end')",
    ],
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


def backup_db(db_path: str, version: int) -> str:
    """Create a backup of the database before migration.

    Args:
        db_path: Path to the database file.
        version: Current schema version (used in backup filename).

    Returns:
        Path to the backup file.
    """
    backup_path = f"{db_path}.bak.v{version}"
    shutil.copy2(db_path, backup_path)
    print(f"Backup created: {backup_path}")
    return backup_path


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
        sys.exit(1)

    print(f"Migrating: v{current} -> v{EXPECTED_VERSION}")

    # Create backup before applying migration
    backup_db(db_path, current)

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
            cursor.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
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


def check_and_migrate(db_path: str = DB_PATH):
    """Check schema version and report status. Does NOT migrate -- init_db.py handles that."""
    if not os.path.exists(db_path):
        # Fresh DB - init_db.py will create it. Silent success.
        return
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    current = get_current_version(conn)
    if current == EXPECTED_VERSION:
        print(f"Already at schema v{current}.")
        conn.close()
        return
    if current > EXPECTED_VERSION:
        print(f"DB schema v{current} is newer than expected v{EXPECTED_VERSION}.")
        print("This might mean you're running an older version of the skill.")
        conn.close()
        sys.exit(1)
    # Behind or fresh (version 0) -- init_db.py will handle migration via CREATE TABLE IF NOT EXISTS
    print(f"DB schema v{current} is behind expected v{EXPECTED_VERSION}. init_db.py will handle upgrade.")
    conn.close()
    sys.exit(1)


def migrate_down(db_path: str = DB_PATH):
    """Down-migrate from current version to previous version."""
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}. Run init_db.py first.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=OFF")  # Disable FK checks during table rebuild
    conn.execute("PRAGMA busy_timeout=5000")

    current = get_current_version(conn)

    if current <= 1:
        print(f"Already at schema v{current}. Nothing to revert.")
        conn.close()
        return

    target_version = current - 1
    print(f"Down-migrating: v{current} -> v{target_version}")

    # Create backup before down-migration
    backup_db(db_path, current)

    if current in REVERSE_MIGRATIONS:
        cursor = conn.cursor()
        print(f"  Reverting migration from v{current}...")
        for sql in REVERSE_MIGRATIONS[current]:
            try:
                cursor.execute(sql)
                print(f"    OK: {sql[:80]}...")
            except sqlite3.OperationalError as e:
                print(f"    ERROR: {e}")
                print(f"    SQL: {sql}")
                conn.close()
                sys.exit(1)
            except sqlite3.IntegrityError as e:
                # Handle potential FK constraint issues during table recreation
                if "foreign key" in str(e).lower():
                    print(f"    FK note: {e}")
                else:
                    print(f"    ERROR: {e}")
                    print(f"    SQL: {sql}")
                    conn.close()
                    sys.exit(1)

        # Update version
        cursor.execute("UPDATE schema_version SET version = ?", (target_version,))

        # Re-enable foreign keys and verify
        conn.execute("PRAGMA foreign_keys=ON")
        conn.commit()
        print(f"Down-migration complete. Now at v{target_version}.")
    else:
        print(f"  No reverse migration steps for v{current}")

    conn.close()


if __name__ == "__main__":
    path = DB_PATH
    down = "--down" in sys.argv
    check = "--check" in sys.argv
    if "--db" in sys.argv:
        idx = sys.argv.index("--db")
        if idx + 1 < len(sys.argv):
            path = sys.argv[idx + 1]
    if check:
        check_and_migrate(path)
    elif down:
        migrate_down(path)
    else:
        migrate(path)
