#!/usr/bin/env python3
"""Tests for migrate_db.py v1->v2 migration.

Tests cover:
- EXPECTED_VERSION is 2
- MIGRATIONS[2] has all 8 statements (4 ALTER TABLE + 4 INSERT OR IGNORE)
- Migration adds modules.next_review_date (TEXT)
- Migration adds modules.score (REAL DEFAULT 0)
- Migration adds daily_tasks.response_window_end (TEXT)
- Migration adds daily_tasks.feedback (TEXT)
- Migration inserts missing config keys
- backup_db() creates backup before migration
- --down flag reverses v2 migration
- --down creates backup at .bak.v2
- Running migrate twice is idempotent
- --down on a v1 DB prints message and exits
"""

import os
import sqlite3
import subprocess
import sys
import tempfile
import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")


def _create_v1_db(db_path: str) -> sqlite3.Connection:
    """Create a v1 database matching the original schema (before migration)."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("""CREATE TABLE IF NOT EXISTS paths (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'draft',
        is_active INTEGER DEFAULT 0,
        confirmed INTEGER DEFAULT 0,
        created TEXT,
        completed TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS modules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        module_order INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        score_avg REAL DEFAULT 0,
        times_repeated INTEGER DEFAULT 0,
        started TEXT,
        completed TEXT,
        FOREIGN KEY (path_id) REFERENCES paths(id) ON DELETE CASCADE
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_id INTEGER NOT NULL,
        url TEXT NOT NULL,
        title TEXT,
        type TEXT,
        verified TEXT DEFAULT 'pending',
        FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS daily_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        content TEXT NOT NULL,
        response TEXT,
        score INTEGER,
        feedback TEXT,
        skipped INTEGER DEFAULT 0,
        awaiting_response INTEGER DEFAULT 1,
        FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
    )""")

    c.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")

    # Insert default config values
    defaults = [
        ('active_path_id', ''),
        ('pending_task_id', ''),
        ('last_response_date', ''),
        ('streak_count', '0'),
    ]
    for key, value in defaults:
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (key, value))

    # Insert sample data to verify it survives migration
    c.execute("INSERT INTO paths (topic, description, status, is_active, confirmed, created) VALUES (?, ?, ?, ?, ?, ?)",
              ("Python", "Learn Python basics", "active", 1, 1, "2026-01-01"))
    c.execute("INSERT INTO modules (path_id, title, description, module_order, status, score_avg) VALUES (?, ?, ?, ?, ?, ?)",
              (1, "Variables", "Learn about variables", 1, "in_progress", 7.5))
    c.execute("INSERT INTO daily_tasks (module_id, date, content, score, feedback, skipped, awaiting_response) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (1, "2026-01-01", "What is a variable?", 8, "Good answer", 0, 0))

    # Set schema version to 1
    c.execute("INSERT INTO schema_version (version) VALUES (1)")

    conn.commit()
    return conn


class TestMigrationConstants:
    """Test that migration constants are correctly set."""

    def test_expected_version_is_2(self):
        """EXPECTED_VERSION must be 2."""
        sys.path.insert(0, SCRIPTS_DIR)
        import migrate_db
        assert migrate_db.EXPECTED_VERSION == 2

    def test_migrations_v2_has_8_statements(self):
        """MIGRATIONS[2] must have exactly 8 statements."""
        sys.path.insert(0, SCRIPTS_DIR)
        import migrate_db
        assert 2 in migrate_db.MIGRATIONS
        assert len(migrate_db.MIGRATIONS[2]) == 8

    def test_migrations_v2_alters_modules_score(self):
        """MIGRATIONS[2] must include ALTER TABLE modules ADD COLUMN score."""
        sys.path.insert(0, SCRIPTS_DIR)
        import migrate_db
        sqls = migrate_db.MIGRATIONS[2]
        assert any("ALTER TABLE modules ADD COLUMN score" in s for s in sqls)

    def test_migrations_v2_alters_modules_next_review_date(self):
        """MIGRATIONS[2] must include ALTER TABLE modules ADD COLUMN next_review_date."""
        sys.path.insert(0, SCRIPTS_DIR)
        import migrate_db
        sqls = migrate_db.MIGRATIONS[2]
        assert any("ALTER TABLE modules ADD COLUMN next_review_date" in s for s in sqls)

    def test_migrations_v2_alters_daily_tasks_response_window_end(self):
        """MIGRATIONS[2] must include ALTER TABLE daily_tasks ADD COLUMN response_window_end."""
        sys.path.insert(0, SCRIPTS_DIR)
        import migrate_db
        sqls = migrate_db.MIGRATIONS[2]
        assert any("ALTER TABLE daily_tasks ADD COLUMN response_window_end" in s for s in sqls)

    def test_migrations_v2_alters_daily_tasks_feedback(self):
        """MIGRATIONS[2] must include ALTER TABLE daily_tasks ADD COLUMN feedback."""
        sys.path.insert(0, SCRIPTS_DIR)
        import migrate_db
        sqls = migrate_db.MIGRATIONS[2]
        assert any("ALTER TABLE daily_tasks ADD COLUMN feedback" in s for s in sqls)

    def test_migrations_v2_inserts_config_keys(self):
        """MIGRATIONS[2] must INSERT OR IGNORE config keys: last_task_date, daily_count, weekly_count, response_window_end."""
        sys.path.insert(0, SCRIPTS_DIR)
        import migrate_db
        sqls = migrate_db.MIGRATIONS[2]
        assert any("last_task_date" in s and "INSERT OR IGNORE" in s for s in sqls)
        assert any("daily_count" in s and "INSERT OR IGNORE" in s for s in sqls)
        assert any("weekly_count" in s and "INSERT OR IGNORE" in s for s in sqls)
        assert any("response_window_end" in s and "INSERT OR IGNORE" in s for s in sqls)


class TestMigrationUp:
    """Test v1->v2 up-migration."""

    def test_migration_adds_modules_columns(self):
        """After migration, modules table has score and next_review_date columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            migrate_db.migrate(db_path)

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("PRAGMA table_info(modules)")
            cols = {row[1]: row[2] for row in c.fetchall()}

            assert "score" in cols, "modules.score column missing after migration"
            assert "next_review_date" in cols, "modules.next_review_date column missing after migration"
            conn.close()

    def test_migration_adds_daily_tasks_columns(self):
        """After migration, daily_tasks table has response_window_end column."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            migrate_db.migrate(db_path)

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("PRAGMA table_info(daily_tasks)")
            cols = {row[1]: row[2] for row in c.fetchall()}

            assert "response_window_end" in cols, "daily_tasks.response_window_end column missing after migration"
            conn.close()

    def test_migration_adds_config_keys(self):
        """After migration, config table has new keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            migrate_db.migrate(db_path)

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT key FROM config ORDER BY key")
            keys = [row[0] for row in c.fetchall()]

            assert "last_task_date" in keys
            assert "daily_count" in keys
            assert "weekly_count" in keys
            assert "response_window_end" in keys
            conn.close()

    def test_migration_preserves_existing_data(self):
        """Existing rows survive migration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            migrate_db.migrate(db_path)

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM paths")
            assert c.fetchone()[0] == 1
            c.execute("SELECT COUNT(*) FROM modules")
            assert c.fetchone()[0] == 1
            c.execute("SELECT COUNT(*) FROM daily_tasks")
            assert c.fetchone()[0] == 1
            c.execute("SELECT score FROM daily_tasks")
            assert c.fetchone()[0] == 8
            conn.close()

    def test_migration_creates_backup(self):
        """Migration creates backup file at .bak.v1 before applying."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            backup_path = f"{db_path}.bak.v1"
            assert not os.path.exists(backup_path)

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            migrate_db.migrate(db_path)

            assert os.path.exists(backup_path), f"Backup file not created at {backup_path}"

    def test_migration_is_idempotent(self):
        """Running migration twice does not fail (SKIP for duplicate columns, IGNORE for duplicate config)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            migrate_db.migrate(db_path)
            migrate_db.migrate(db_path)  # Second run should not fail

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT version FROM schema_version")
            version = c.fetchone()[0]
            assert version == 2
            conn.close()


class TestMigrationDown:
    """Test v2->v1 down-migration."""

    def test_down_migration_removes_modules_columns(self):
        """After down-migration, modules table no longer has score and next_review_date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            migrate_db.migrate(db_path)
            migrate_db.migrate_down(db_path)

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("PRAGMA table_info(modules)")
            cols = {row[1] for row in c.fetchall()}

            assert "score" not in cols, "modules.score should be removed by down-migration"
            assert "next_review_date" not in cols, "modules.next_review_date should be removed by down-migration"
            conn.close()

    def test_down_migration_removes_daily_tasks_columns(self):
        """After down-migration, daily_tasks no longer has response_window_end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            migrate_db.migrate(db_path)
            migrate_db.migrate_down(db_path)

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("PRAGMA table_info(daily_tasks)")
            cols = {row[1] for row in c.fetchall()}

            assert "response_window_end" not in cols, "daily_tasks.response_window_end should be removed"
            conn.close()

    def test_down_migration_removes_config_keys(self):
        """After down-migration, new config keys are removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            migrate_db.migrate(db_path)
            migrate_db.migrate_down(db_path)

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT key FROM config ORDER BY key")
            keys = [row[0] for row in c.fetchall()]

            assert "last_task_date" not in keys
            assert "daily_count" not in keys
            assert "weekly_count" not in keys
            assert "response_window_end" not in keys
            conn.close()

    def test_down_migration_sets_version_to_1(self):
        """After down-migration, schema_version is 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            migrate_db.migrate(db_path)
            migrate_db.migrate_down(db_path)

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT version FROM schema_version")
            version = c.fetchone()[0]
            assert version == 1
            conn.close()

    def test_down_migration_creates_backup(self):
        """Down-migration creates backup at .bak.v2."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            migrate_db.migrate(db_path)

            backup_path = f"{db_path}.bak.v2"
            assert not os.path.exists(backup_path)

            migrate_db.migrate_down(db_path)

            assert os.path.exists(backup_path), f"Down-migration backup not created at {backup_path}"

    def test_down_on_v1_db_exits_gracefully(self):
        """Running --down on a v1 DB prints message and does not crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            # Should not raise an exception
            migrate_db.migrate_down(db_path)

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT version FROM schema_version")
            assert c.fetchone()[0] == 1
            conn.close()

    def test_down_migration_preserves_existing_data(self):
        """Data survives down-migration (except values in removed columns)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            migrate_db.migrate(db_path)
            migrate_db.migrate_down(db_path)

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM paths")
            assert c.fetchone()[0] == 1
            c.execute("SELECT COUNT(*) FROM modules")
            assert c.fetchone()[0] == 1
            c.execute("SELECT COUNT(*) FROM daily_tasks")
            assert c.fetchone()[0] == 1
            conn.close()

    def test_down_migration_recreates_indexes(self):
        """After down-migration, foreign key indexes are recreated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = _create_v1_db(db_path)
            conn.close()

            sys.path.insert(0, SCRIPTS_DIR)
            import migrate_db
            migrate_db.migrate(db_path)
            migrate_db.migrate_down(db_path)

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
            index_names = [row[0] for row in c.fetchall()]

            # These indexes should exist after down-migration
            assert any("idx_modules" in name or "modules" in name for name in index_names), \
                f"modules index missing after down-migration. Found indexes: {index_names}"
            assert any("idx_daily_tasks" in name or "daily_tasks" in name for name in index_names), \
                f"daily_tasks index missing after down-migration. Found indexes: {index_names}"
            conn.close()
