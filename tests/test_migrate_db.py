#!/usr/bin/env python3
"""Tests for migrate_db.py v1->v2 migration."""
import sqlite3
import os
import sys
import tempfile
import shutil

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import importlib
migrate_db = importlib.import_module("migrate_db")


def create_v1_db(db_path: str):
    """Create a minimal v1 database matching the current schema (before v2 migration)."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    c.execute("""
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
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS modules (
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
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            title TEXT,
            type TEXT,
            verified TEXT DEFAULT 'pending',
            FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_tasks (
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
        )
    """)

    # Insert v1-only config keys
    for key, value in [
        ("active_path_id", "1"),
        ("pending_task_id", "5"),
        ("last_response_date", "2026-04-10"),
        ("streak_count", "3"),
    ]:
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (key, value))

    # Insert sample data
    c.execute(
        "INSERT INTO paths (topic, status, is_active) VALUES (?, ?, ?)",
        ("Python", "active", 1),
    )
    c.execute(
        "INSERT INTO modules (path_id, title, module_order, status, score_avg) VALUES (?, ?, ?, ?, ?)",
        (1, "Basics", 1, "completed", 7.5),
    )
    c.execute(
        "INSERT INTO daily_tasks (module_id, date, content, score) VALUES (?, ?, ?, ?)",
        (1, "2026-04-10", "Write a function", 8),
    )

    # Set schema version to 1
    c.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
    c.execute("INSERT INTO schema_version (version) VALUES (1)")

    conn.commit()
    conn.close()


def create_v2_db(db_path: str):
    """Create a minimal v2 database with all tables and schema_version=2."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    c.execute("""
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
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS modules (
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
            score REAL DEFAULT 0,
            next_review_date TEXT,
            FOREIGN KEY (path_id) REFERENCES paths(id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            title TEXT,
            type TEXT,
            verified TEXT DEFAULT 'pending',
            FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            content TEXT NOT NULL,
            response TEXT,
            score INTEGER,
            feedback TEXT,
            skipped INTEGER DEFAULT 0,
            awaiting_response INTEGER DEFAULT 1,
            response_window_end TEXT,
            FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
        )
    """)
    c.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
    c.execute("INSERT INTO schema_version (version) VALUES (2)")
    conn.commit()
    conn.close()


class TestMigrationV2:
    """Test suite for v1->v2 migration."""

    def test_expected_version_is_3(self):
        assert migrate_db.EXPECTED_VERSION == 3, (
            f"EXPECTED_VERSION should be 3, got {migrate_db.EXPECTED_VERSION}"
        )

    def test_migrations_v2_has_8_statements(self):
        assert 2 in migrate_db.MIGRATIONS, "MIGRATIONS dict must have key 2"
        stmts = migrate_db.MIGRATIONS[2]
        assert len(stmts) == 8, f"MIGRATIONS[2] should have 8 statements, got {len(stmts)}"

    def test_migration_v2_adds_modules_score(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        create_v1_db(db_path)
        migrate_db.migrate(db_path)
        conn = sqlite3.connect(db_path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(modules)").fetchall()]
        assert "score" in cols, "modules.score column missing after migration"
        conn.close()

    def test_migration_v2_adds_modules_next_review_date(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        create_v1_db(db_path)
        migrate_db.migrate(db_path)
        conn = sqlite3.connect(db_path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(modules)").fetchall()]
        assert "next_review_date" in cols, "modules.next_review_date column missing after migration"
        conn.close()

    def test_migration_v2_adds_daily_tasks_response_window_end(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        create_v1_db(db_path)
        migrate_db.migrate(db_path)
        conn = sqlite3.connect(db_path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(daily_tasks)").fetchall()]
        assert "response_window_end" in cols, "daily_tasks.response_window_end column missing after migration"
        conn.close()

    def test_migration_v2_adds_daily_tasks_feedback(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        create_v1_db(db_path)
        migrate_db.migrate(db_path)
        conn = sqlite3.connect(db_path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(daily_tasks)").fetchall()]
        assert "feedback" in cols, "daily_tasks.feedback column missing after migration"
        conn.close()

    def test_migration_v2_inserts_missing_config_keys(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        create_v1_db(db_path)
        migrate_db.migrate(db_path)
        conn = sqlite3.connect(db_path)
        keys = [r[0] for r in conn.execute("SELECT key FROM config ORDER BY key").fetchall()]
        assert "last_task_date" in keys, "last_task_date config key missing"
        assert "daily_count" in keys, "daily_count config key missing"
        assert "weekly_count" in keys, "weekly_count config key missing"
        assert "response_window_end" in keys, "response_window_end config key missing"
        conn.close()

    def test_migration_creates_backup_before_applying(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        create_v1_db(db_path)
        backup_path = migrate_db.backup_db(db_path, 1)
        assert os.path.exists(backup_path), f"Backup file not created at {backup_path}"
        # Verify backup is a valid SQLite file
        conn = sqlite3.connect(backup_path)
        ver = conn.execute("SELECT version FROM schema_version").fetchone()
        assert ver[0] == 1, "Backup should be at v1"
        conn.close()

    def test_migration_idempotent(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        create_v1_db(db_path)
        migrate_db.migrate(db_path)
        # Run again - should not error
        migrate_db.migrate(db_path)
        conn = sqlite3.connect(db_path)
        ver = conn.execute("SELECT version FROM schema_version").fetchone()
        assert ver[0] == 3, f"Should be at v3 after double migrate, got v{ver[0]}"
        conn.close()

    def test_down_migration_v2_reverses_correctly(self, tmp_path):
        """Down-migrate from v2 reverses the v1->v2 migration."""
        db_path = str(tmp_path / "test.db")
        create_v1_db(db_path)
        # Manually set schema_version to 2 before down-migrating
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
        conn.execute("INSERT INTO schema_version (version) VALUES (2)")
        conn.commit()
        conn.close()
        # Now down-migrate (v2 -> v1)
        migrate_db.migrate_down(db_path)
        conn = sqlite3.connect(db_path)
        ver = conn.execute("SELECT version FROM schema_version").fetchone()
        assert ver[0] == 1, f"After --down from v2, should be at v1, got v{ver[0]}"
        # New columns should be gone
        cols = [r[1] for r in conn.execute("PRAGMA table_info(modules)").fetchall()]
        assert "score" not in cols, "modules.score should be removed by --down"
        assert "next_review_date" not in cols, "modules.next_review_date should be removed by --down"
        dt_cols = [r[1] for r in conn.execute("PRAGMA table_info(daily_tasks)").fetchall()]
        assert "response_window_end" not in dt_cols, "daily_tasks.response_window_end should be removed by --down"
        # Config keys should be removed
        keys = [r[0] for r in conn.execute("SELECT key FROM config").fetchall()]
        assert "last_task_date" not in keys, "last_task_date should be removed by --down"
        assert "daily_count" not in keys, "daily_count should be removed by --down"
        assert "weekly_count" not in keys, "weekly_count should be removed by --down"
        assert "response_window_end" not in keys, "response_window_end config should be removed by --down"
        # Existing data should be preserved
        assert conn.execute("SELECT COUNT(*) FROM paths").fetchone()[0] == 1, "paths data lost"
        assert conn.execute("SELECT COUNT(*) FROM modules").fetchone()[0] == 1, "modules data lost"
        conn.close()

    def test_down_migration_creates_backup(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        create_v1_db(db_path)
        migrate_db.migrate(db_path)  # goes to v3
        migrate_db.migrate_down(db_path)  # goes v3 -> v2
        backup_path = str(tmp_path / "test.db.bak.v3")
        assert os.path.exists(backup_path), f"Backup file not created at {backup_path}"

    def test_down_on_v1_db_exits_gracefully(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        create_v1_db(db_path)
        # Should print message and exit without error
        try:
            migrate_db.migrate_down(db_path)
        except SystemExit:
            pass  # Expected -- v1 DB has nothing to revert

    def test_existing_data_preserved_after_migration(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        create_v1_db(db_path)
        migrate_db.migrate(db_path)
        conn = sqlite3.connect(db_path)
        # Check data is intact
        path = conn.execute("SELECT topic FROM paths WHERE id=1").fetchone()
        assert path[0] == "Python", "Path data corrupted"
        module = conn.execute("SELECT title, score_avg FROM modules WHERE id=1").fetchone()
        assert module[0] == "Basics", "Module data corrupted"
        assert module[1] == 7.5, "Module score_avg corrupted"
        task = conn.execute("SELECT score FROM daily_tasks WHERE id=1").fetchone()
        assert task[0] == 8, "Task data corrupted"
        conn.close()

    def test_migration_score_default_is_0(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        create_v1_db(db_path)
        migrate_db.migrate(db_path)
        conn = sqlite3.connect(db_path)
        # Check default value on existing row
        score = conn.execute("SELECT score FROM modules WHERE id=1").fetchone()[0]
        assert score == 0, f"Default score should be 0, got {score}"
        conn.close()


class TestCheckFlag:
    """Test suite for migrate_db.py --check flag."""

    def test_check_flag_exits_0_on_fresh_db(self, tmp_path):
        """--check on non-existent DB should exit 0 silently."""
        db_path = str(tmp_path / "nonexistent.db")
        # Should not raise, should not print
        try:
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                migrate_db.check_and_migrate(db_path)
            output = f.getvalue()
            assert output == "", f"Expected silent output on fresh DB, got: {output}"
        except SystemExit:
            raise AssertionError("--check should not exit on fresh DB")

    def test_check_flag_prints_already_current(self, tmp_path):
        """--check on current DB (v3) should print 'Already at schema v3' and exit 0."""
        db_path = str(tmp_path / "current.db")
        # Create v3 DB directly (matching EXPECTED_VERSION)
        create_v1_db(db_path)
        migrate_db.migrate(db_path)  # This goes to v3
        import io
        import contextlib
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            migrate_db.check_and_migrate(db_path)
        output = f.getvalue()
        assert "Already at schema v3" in output, f"Expected 'Already at schema v3', got: {output}"

    def test_check_flag_does_not_migrate_behind_schema(self, tmp_path):
        """--check on behind DB should NOT migrate - init_db.py handles that."""
        db_path = str(tmp_path / "behind.db")
        create_v1_db(db_path)
        import io
        import contextlib
        f = io.StringIO()
        try:
            with contextlib.redirect_stdout(f):
                migrate_db.check_and_migrate(db_path)
            raise AssertionError("Should have exited with code 1")
        except SystemExit as e:
            assert e.code == 1, f"Expected exit code 1, got {e.code}"
        output = f.getvalue()
        assert "behind expected v3" in output, f"Expected 'behind expected v3', got: {output}"
        # Verify DB was NOT migrated (still at v1)
        conn = sqlite3.connect(db_path)
        ver = conn.execute("SELECT version FROM schema_version").fetchone()
        assert ver[0] == 1, f"Expected v1 (no migration), got v{ver[0]}"
        conn.close()

    def test_check_flag_exits_1_on_newer_schema(self, tmp_path):
        """--check on DB newer than EXPECTED_VERSION should exit 1."""
        db_path = str(tmp_path / "newer.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
        conn.execute("INSERT INTO schema_version (version) VALUES (999)")
        conn.commit()
        conn.close()
        try:
            migrate_db.check_and_migrate(db_path)
            raise AssertionError("Should have exited with code 1")
        except SystemExit as e:
            assert e.code == 1, f"Expected exit code 1, got {e.code}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-x", "-v"])
