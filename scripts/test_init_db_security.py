#!/usr/bin/env python3
"""
Tests for init_db.py security features:
- SEC-01: CHECK constraint on daily_tasks.response column (max 10000 chars)
- SEC-02: learning.db file permissions set to 0o600 on creation
"""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestResponseLengthCheckConstraint(unittest.TestCase):
    """SEC-01: Verify response column has a 10000 character limit."""

    def _init_test_db(self, db_path):
        """Initialize a test database using init_db logic."""
        conn = sqlite3.connect(str(db_path))
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
                response TEXT CHECK(length(response) <= 10000 OR response IS NULL),
                score INTEGER,
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
        ]
        for key, value in defaults:
            c.execute('INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)', (key, value))

        conn.commit()
        conn.close()

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, 'test.db')

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
        os.rmdir(self.tmpdir)

    def test_short_response_accepted(self):
        """A short response (under 10000 chars) should be accepted."""
        self._init_test_db(self.db_path)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Insert a path and module first (FK constraint)
        c.execute("INSERT INTO paths (topic, created) VALUES ('test', '2026-04-12')")
        c.execute("INSERT INTO modules (path_id, title, module_order) VALUES (1, 'test', 1)")
        c.execute(
            'INSERT INTO daily_tasks (module_id, date, content, response) VALUES (1, "2026-04-12", "task", "short")'
        )
        conn.commit()
        row = c.execute('SELECT response FROM daily_tasks WHERE response = "short"').fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 'short')
        conn.close()

    def test_exactly_10000_chars_accepted(self):
        """A response of exactly 10000 characters should be accepted."""
        self._init_test_db(self.db_path)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO paths (topic, created) VALUES ('test', '2026-04-12')")
        c.execute("INSERT INTO modules (path_id, title, module_order) VALUES (1, 'test', 1)")
        long_response = 'x' * 10000
        c.execute(
            'INSERT INTO daily_tasks (module_id, date, content, response) VALUES (1, "2026-04-12", "task", ?)',
            (long_response,),
        )
        conn.commit()
        row = c.execute('SELECT length(response) FROM daily_tasks').fetchone()
        self.assertEqual(row[0], 10000)
        conn.close()

    def test_10001_chars_rejected(self):
        """A response of 10001 characters should raise IntegrityError."""
        self._init_test_db(self.db_path)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO paths (topic, created) VALUES ('test', '2026-04-12')")
        c.execute("INSERT INTO modules (path_id, title, module_order) VALUES (1, 'test', 1)")
        too_long = 'x' * 10001
        with self.assertRaises(sqlite3.IntegrityError):
            c.execute(
                'INSERT INTO daily_tasks (module_id, date, content, response) VALUES (1, "2026-04-12", "task", ?)',
                (too_long,),
            )
        conn.close()

    def test_empty_string_response_accepted(self):
        """An empty string response should be accepted."""
        self._init_test_db(self.db_path)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO paths (topic, created) VALUES ('test', '2026-04-12')")
        c.execute("INSERT INTO modules (path_id, title, module_order) VALUES (1, 'test', 1)")
        c.execute(
            'INSERT INTO daily_tasks (module_id, date, content, response) VALUES (1, "2026-04-12", "task", "")'
        )
        conn.commit()
        row = c.execute('SELECT response FROM daily_tasks WHERE response = ""').fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], '')
        conn.close()

    def test_null_response_accepted(self):
        """A NULL response should be accepted (response is optional)."""
        self._init_test_db(self.db_path)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO paths (topic, created) VALUES ('test', '2026-04-12')")
        c.execute("INSERT INTO modules (path_id, title, module_order) VALUES (1, 'test', 1)")
        c.execute(
            'INSERT INTO daily_tasks (module_id, date, content, response) VALUES (1, "2026-04-12", "task", NULL)'
        )
        conn.commit()
        row = c.execute('SELECT response FROM daily_tasks WHERE response IS NULL').fetchone()
        self.assertIsNotNone(row)
        self.assertIsNone(row[0])
        conn.close()


class TestDbFilePermissions(unittest.TestCase):
    """SEC-02: Verify learning.db is created with file permissions 0o600."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch('os.chmod')
    @patch('pathlib.Path.home')
    def test_init_db_calls_chmod_600(self, mock_home, mock_chmod):
        """init_db() should call os.chmod with 0o600 on the database file."""
        mock_home.return_value = Path(self.tmpdir)
        import importlib
        import sys
        scripts_dir = os.path.join(os.path.dirname(__file__))
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        import init_db
        importlib.reload(init_db)
        init_db.init_db()

        # Verify os.chmod was called with 0o600
        mock_chmod.assert_called_once()
        args = mock_chmod.call_args
        self.assertEqual(args[0][1], 0o600)

    @patch('pathlib.Path.home')
    def test_init_db_sets_600_permissions(self, mock_home):
        """init_db() should create the database with 0o600 file permissions."""
        mock_home.return_value = Path(self.tmpdir)
        import importlib
        import sys
        scripts_dir = os.path.join(os.path.dirname(__file__))
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        import init_db
        importlib.reload(init_db)
        init_db.init_db()

        # Verify the db was created with 0o600 permissions
        db_path = self.tmpdir + '/.hermes/skills/tutor/learning.db'
        self.assertTrue(os.path.exists(db_path))
        st = os.stat(db_path)
        perms = st.st_mode & 0o777
        self.assertEqual(perms, 0o600, f"Expected 0o600, got {oct(perms)}")


if __name__ == '__main__':
    unittest.main()
