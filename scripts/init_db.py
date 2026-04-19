#!/usr/bin/env python3
"""
Initialize the learning path database.
Idempotent - safe to run multiple times.
"""
import sqlite3
import os
from pathlib import Path

def init_db():
    db_dir = Path.home() / ".hermes" / "skills" / "tutor"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "learning.db"

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON")
    c = conn.cursor()

    # Config table for state management
    c.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # Learning paths
    c.execute('''
        CREATE TABLE IF NOT EXISTS paths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'draft',
            is_active INTEGER DEFAULT 0,
            confirmed INTEGER DEFAULT 0,
            created TEXT,
            completed TEXT
        )
    ''')

    # Modules within a path
    c.execute('''
        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            module_order INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            score_avg REAL DEFAULT 0,
            score REAL DEFAULT 0,
            next_review_date TEXT,
            times_repeated INTEGER DEFAULT 0,
            started TEXT,
            completed TEXT,
            FOREIGN KEY (path_id) REFERENCES paths(id) ON DELETE CASCADE
        )
    ''')

    # Resources for each module
    c.execute('''
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            title TEXT,
            type TEXT,
            verified TEXT DEFAULT 'pending',
            FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
        )
    ''')

    # Daily tasks
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            content TEXT NOT NULL,
            response TEXT CHECK(length(response) <= 10000 OR response IS NULL),
            score INTEGER,
            feedback TEXT,
            response_window_end TEXT,
            skipped INTEGER DEFAULT 0,
            awaiting_response INTEGER DEFAULT 1,
            FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
        )
    ''')

    # Insert default config values if not exist
    defaults = [
        ('active_path_id', ''),
        ('pending_task_id', ''),
        ('last_response_date', ''),
        ('streak_count', '0'),
        ('last_task_date', ''),
        ('daily_count', '0'),
        ('weekly_count', '0'),
        ('response_window_end', ''),
        ('locale', 'es'),
    ]
    for key, value in defaults:
        c.execute('INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)', (key, value))

    conn.commit()

    # Set schema version to 3 (matches EXPECTED_VERSION in migrate_db.py)
    c.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
    c.execute("DELETE FROM schema_version")
    c.execute("INSERT INTO schema_version (version) VALUES (3)")
    conn.commit()

    conn.close()

    # Set file permissions: owner read/write only
    os.chmod(str(db_path), 0o600)

    print(f"Database initialized at: {db_path}")

if __name__ == "__main__":
    init_db()
