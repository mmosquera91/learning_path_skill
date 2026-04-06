#!/usr/bin/env python3
"""Initialize the Learning Path Generator SQLite database.

Usage:
    python3 init_db.py [--db PATH]

Default DB: ~/.hermes/skills/tutor/learning.db
"""

import sqlite3
import os
import sys

DB_PATH = os.path.expanduser("~/.hermes/skills/tutor/learning.db")

SCHEMA_VERSION = 1

SCHEMA = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

-- Global config (key-value store for runtime state)
CREATE TABLE IF NOT EXISTS config (
    key   TEXT PRIMARY KEY,
    value TEXT
);

-- Learning paths (one per topic)
CREATE TABLE IF NOT EXISTS paths (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    topic       TEXT NOT NULL,
    status      TEXT DEFAULT 'active',
    is_active   INTEGER DEFAULT 1,
    confirmed   INTEGER DEFAULT 0,
    created     TEXT,
    completed   TEXT
);

-- Modules within a path
CREATE TABLE IF NOT EXISTS modules (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    path_id          INTEGER REFERENCES paths(id) ON DELETE CASCADE,
    title            TEXT NOT NULL,
    description      TEXT,
    module_order     INTEGER,
    status           TEXT DEFAULT 'pending',
    score            REAL,
    score_avg        REAL,
    next_review_date TEXT,
    times_repeated   INTEGER DEFAULT 0,
    started          TEXT,
    completed        TEXT
);

-- Daily tasks / assignments
CREATE TABLE IF NOT EXISTS daily_tasks (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id           INTEGER REFERENCES modules(id) ON DELETE CASCADE,
    date                TEXT,
    content             TEXT,
    response            TEXT,
    feedback            TEXT,
    score               REAL,
    awaiting_response   INTEGER DEFAULT 1,
    response_window_end TEXT,
    skipped             INTEGER DEFAULT 0
);

-- Learning resources per module
CREATE TABLE IF NOT EXISTS resources (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER REFERENCES modules(id) ON DELETE CASCADE,
    url       TEXT,
    title     TEXT,
    type      TEXT,
    verified  TEXT DEFAULT 'pending'
);

-- Initial config defaults
INSERT OR IGNORE INTO config (key, value) VALUES ('active_path_id', '');
INSERT OR IGNORE INTO config (key, value) VALUES ('pending_task_id', '');
INSERT OR IGNORE INTO config (key, value) VALUES ('last_task_date', '');
INSERT OR IGNORE INTO config (key, value) VALUES ('last_response_date', '');
INSERT OR IGNORE INTO config (key, value) VALUES ('daily_count', '0');
INSERT OR IGNORE INTO config (key, value) VALUES ('weekly_count', '0');
"""


def init_db(db_path: str = DB_PATH):
    """Create or verify the database."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    cursor = conn.cursor()

    # Check if already initialized
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if cursor.fetchone():
        print(f"DB already exists at {db_path}")
        cursor.execute("SELECT version FROM schema_version")
        row = cursor.fetchone()
        current = row[0] if row else 0
        print(f"Schema version: {current}")
        conn.close()
        return

    # Fresh init
    cursor.executescript(SCHEMA)
    cursor.execute(
        "INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,)
    )
    conn.commit()
    conn.close()
    print(f"DB initialized at {db_path} (schema v{SCHEMA_VERSION})")


if __name__ == "__main__":
    path = DB_PATH
    if "--db" in sys.argv:
        idx = sys.argv.index("--db")
        if idx + 1 < len(sys.argv):
            path = sys.argv[idx + 1]
    init_db(path)
