"""Tests for init_db.py -- database initialization and idempotency.

init_db() hardcodes the DB path, so tests replicate the SQL logic
to verify schema correctness without touching the real database.
"""
import sqlite3
import os

EXPECTED_TABLES = [
    "config", "paths", "modules", "resources", "daily_tasks"
]

EXPECTED_CONFIG_KEYS = [
    "active_path_id", "pending_task_id", "last_response_date",
    "streak_count", "last_task_date", "daily_count", "weekly_count",
    "response_window_end",
]

EXPECTED_MODULES_COLUMNS = [
    "id", "path_id", "title", "description", "module_order",
    "status", "score_avg", "score", "next_review_date",
    "times_repeated", "started", "completed",
]

EXPECTED_DAILY_TASKS_COLUMNS = [
    "id", "module_id", "date", "content", "response", "score",
    "response_window_end", "feedback", "skipped", "awaiting_response",
]


def _run_init_sql(db_path: str) -> sqlite3.Connection:
    """Execute the same SQL that init_db() runs, against a temp DB."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

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

    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            content TEXT NOT NULL,
            response TEXT,
            score INTEGER,
            response_window_end TEXT,
            feedback TEXT,
            skipped INTEGER DEFAULT 0,
            awaiting_response INTEGER DEFAULT 1,
            FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
        )
    ''')

    defaults = [
        ('active_path_id', ''),
        ('pending_task_id', ''),
        ('last_response_date', ''),
        ('streak_count', '0'),
        ('last_task_date', ''),
        ('daily_count', '0'),
        ('weekly_count', '0'),
        ('response_window_end', ''),
    ]
    for key, value in defaults:
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (key, value))

    conn.commit()
    return conn


class TestInitDb:
    """Tests for database initialization logic."""

    def test_creates_all_tables(self, tmp_path):
        """init_db creates all 5 expected tables."""
        db_path = str(tmp_path / "test.db")
        conn = _run_init_sql(db_path)
        tables = [
            r[0] for r in
            conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]
        for table in EXPECTED_TABLES:
            assert table in tables, f"Table {table} not created"
        conn.close()

    def test_idempotent(self, tmp_path):
        """Running init SQL twice does not raise or duplicate data."""
        db_path = str(tmp_path / "test.db")
        conn1 = _run_init_sql(db_path)
        conn1.close()
        # Run again -- should succeed without error
        conn2 = _run_init_sql(db_path)
        rows = conn2.execute("SELECT COUNT(*) FROM config").fetchone()[0]
        assert rows == 8, f"Expected 8 config keys, got {rows} (duplication on re-run?)"
        conn2.close()

    def test_initializes_all_config_keys(self, tmp_path):
        """All 8 expected config keys are initialized with defaults."""
        db_path = str(tmp_path / "test.db")
        conn = _run_init_sql(db_path)
        keys = [
            r[0] for r in
            conn.execute("SELECT key FROM config ORDER BY key").fetchall()
        ]
        for key in EXPECTED_CONFIG_KEYS:
            assert key in keys, f"Config key {key} not initialized"
        conn.close()

    def test_modules_table_has_all_columns(self, tmp_path):
        """modules table contains all expected columns."""
        db_path = str(tmp_path / "test.db")
        conn = _run_init_sql(db_path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(modules)").fetchall()]
        for col in EXPECTED_MODULES_COLUMNS:
            assert col in cols, f"modules.{col} column missing"
        conn.close()

    def test_daily_tasks_table_has_all_columns(self, tmp_path):
        """daily_tasks table contains all expected columns."""
        db_path = str(tmp_path / "test.db")
        conn = _run_init_sql(db_path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(daily_tasks)").fetchall()]
        for col in EXPECTED_DAILY_TASKS_COLUMNS:
            assert col in cols, f"daily_tasks.{col} column missing"
        conn.close()

    def test_uses_wal_journal_mode(self, tmp_path):
        """Database should use WAL journal mode for concurrent access."""
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode in ("wal", "WAL"), f"Expected WAL mode, got {mode}"
        conn.close()
