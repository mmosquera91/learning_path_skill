"""Tests for eval pipeline state transitions (TEST-04).

Tests verify DB state changes from eval.md Steps 3-5 using direct SQL,
no LLM calls. The eval SQL is replicated here to test the state machine.
"""
import sqlite3


def _create_full_schema(conn: sqlite3.Connection):
    """Create all tables matching the current production schema."""
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys=ON")

    c.execute('''CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY, value TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS paths (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL, description TEXT,
        status TEXT DEFAULT 'draft', is_active INTEGER DEFAULT 0,
        confirmed INTEGER DEFAULT 0, created TEXT, completed TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS modules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path_id INTEGER NOT NULL, title TEXT NOT NULL, description TEXT,
        module_order INTEGER NOT NULL, status TEXT DEFAULT 'pending',
        score_avg REAL DEFAULT 0, score REAL DEFAULT 0,
        next_review_date TEXT, times_repeated INTEGER DEFAULT 0,
        started TEXT, completed TEXT,
        FOREIGN KEY (path_id) REFERENCES paths(id) ON DELETE CASCADE
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_id INTEGER NOT NULL, url TEXT NOT NULL, title TEXT,
        type TEXT, verified TEXT DEFAULT 'pending',
        FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_id INTEGER NOT NULL, date TEXT NOT NULL,
        content TEXT NOT NULL, response TEXT, score INTEGER,
        response_window_end TEXT, feedback TEXT,
        skipped INTEGER DEFAULT 0, awaiting_response INTEGER DEFAULT 1,
        FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
    )''')
    conn.commit()


def _setup_eval_scenario(
    db_path: str,
    initial_score_avg: float = 0.0,
    times_repeated: int = 0,
) -> tuple[int, int]:
    """Create path + module + pending task. Returns (module_id, task_id)."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    _create_full_schema(conn)
    c = conn.cursor()

    c.execute(
        "INSERT INTO paths (topic, status, is_active) VALUES (?, ?, ?)",
        ("test_topic", "active", 1),
    )
    path_id = c.lastrowid

    c.execute(
        """INSERT INTO modules
           (path_id, title, module_order, status, score_avg, times_repeated)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (path_id, "Test Module", 1, "in_progress", initial_score_avg, times_repeated),
    )
    module_id = c.lastrowid

    c.execute(
        """INSERT INTO daily_tasks
           (module_id, date, content, awaiting_response)
           VALUES (?, ?, ?, ?)""",
        (module_id, "2026-04-12", "What is X?", 1),
    )
    task_id = c.lastrowid

    conn.commit()
    conn.close()
    return module_id, task_id


def _apply_eval(
    db_path: str,
    task_id: int,
    module_id: int,
    response: str,
    score: float,
    feedback: str,
) -> None:
    """Replicate eval.md Steps 3-4: save evaluation, update module, handle completion."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    c = conn.cursor()

    # Step 3: Save evaluation
    c.execute(
        """UPDATE daily_tasks
           SET response = ?, score = ?, feedback = ?, awaiting_response = 0
           WHERE id = ?""",
        (response, score, feedback, task_id),
    )

    # Step 4: Calculate average score and update module
    c.execute(
        "SELECT AVG(score) FROM daily_tasks WHERE module_id = ? AND score IS NOT NULL",
        (module_id,),
    )
    avg_score = c.fetchone()[0]

    c.execute(
        """UPDATE modules
           SET score_avg = ?,
               status = CASE WHEN ? >= 7 THEN 'completed' ELSE 'in_progress' END,
               completed = CASE WHEN ? >= 7 THEN datetime('now') ELSE NULL END
           WHERE id = ?""",
        (avg_score, score, score, module_id),
    )

    # Step 5: Completion/repeat logic (from eval.md documentation)
    # NOTE: The SQL in eval.md Step 4 does NOT increment times_repeated.
    # Step 5 mentions it only as a description. We test what the SQL does.
    conn.commit()
    conn.close()


class TestEvalStateTransitions:
    """Tests for eval pipeline DB state transitions -- no LLM calls."""

    def test_score_ge7_sets_module_completed(self, tmp_path):
        """Score >= 7 sets module status to 'completed' and sets completed timestamp."""
        db_path = str(tmp_path / "test.db")
        module_id, task_id = _setup_eval_scenario(db_path)
        _apply_eval(db_path, task_id, module_id, "Great answer", 8.0, "Well done")

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT status, completed FROM modules WHERE id = ?", (module_id,)
        ).fetchone()
        conn.close()

        assert row[0] == "completed", f"Expected 'completed', got '{row[0]}'"
        assert row[1] is not None, "completed timestamp should be set"

    def test_score_lt7_keeps_module_in_progress(self, tmp_path):
        """Score < 7 sets module status to 'in_progress' and does NOT set completed timestamp."""
        db_path = str(tmp_path / "test.db")
        module_id, task_id = _setup_eval_scenario(db_path)
        _apply_eval(db_path, task_id, module_id, "Weak answer", 5.0, "Needs work")

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT status, completed FROM modules WHERE id = ?", (module_id,)
        ).fetchone()
        conn.close()

        assert row[0] == "in_progress", f"Expected 'in_progress', got '{row[0]}'"
        assert row[1] is None, "completed timestamp should be NULL"

    def test_score_ge7_updates_score_avg(self, tmp_path):
        """Score >= 7 correctly updates module score_avg (average of all task scores)."""
        db_path = str(tmp_path / "test.db")
        module_id, task_id = _setup_eval_scenario(db_path, initial_score_avg=0.0)
        _apply_eval(db_path, task_id, module_id, "Answer 1", 8.0, "Good")

        conn = sqlite3.connect(db_path)
        avg = conn.execute(
            "SELECT score_avg FROM modules WHERE id = ?", (module_id,)
        ).fetchone()[0]
        conn.close()

        assert avg == 8.0, f"Expected score_avg=8.0, got {avg}"

    def test_score_lt7_does_not_increment_times_repeated_in_sql(self, tmp_path):
        """The eval.md SQL does NOT increment times_repeated -- only Step 5 docs mention it.

        This test documents the actual behavior: the SQL CASE statement in Step 4
        does not touch times_repeated. Step 5's description of incrementing is not
        reflected in the SQL. This is a known gap (Phase 3 work).
        """
        db_path = str(tmp_path / "test.db")
        module_id, task_id = _setup_eval_scenario(db_path, times_repeated=0)
        _apply_eval(db_path, task_id, module_id, "Weak answer", 4.0, "Needs improvement")

        conn = sqlite3.connect(db_path)
        repeated = conn.execute(
            "SELECT times_repeated FROM modules WHERE id = ?", (module_id,)
        ).fetchone()[0]
        conn.close()

        # The SQL does NOT increment times_repeated -- it stays at 0
        assert repeated == 0, (
            f"Expected times_repeated=0 (SQL doesn't increment it), got {repeated}"
        )

    def test_eval_clears_awaiting_response(self, tmp_path):
        """Eval sets awaiting_response to 0 on the daily_task."""
        db_path = str(tmp_path / "test.db")
        module_id, task_id = _setup_eval_scenario(db_path)
        _apply_eval(db_path, task_id, module_id, "My response", 7.0, "OK")

        conn = sqlite3.connect(db_path)
        awaiting = conn.execute(
            "SELECT awaiting_response FROM daily_tasks WHERE id = ?", (task_id,)
        ).fetchone()[0]
        conn.close()

        assert awaiting == 0, f"Expected awaiting_response=0, got {awaiting}"

    def test_eval_stores_response_score_feedback(self, tmp_path):
        """Eval stores response, score, and feedback on the daily_task row."""
        db_path = str(tmp_path / "test.db")
        module_id, task_id = _setup_eval_scenario(db_path)
        _apply_eval(
            db_path, task_id, module_id,
            "My detailed response", 9.0, "Excellent understanding"
        )

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT response, score, feedback FROM daily_tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        conn.close()

        assert row[0] == "My detailed response"
        assert row[1] == 9.0
        assert row[2] == "Excellent understanding"

    def test_boundary_score_7_triggers_completed(self, tmp_path):
        """Score of exactly 7.0 triggers 'completed' status (boundary test)."""
        db_path = str(tmp_path / "test.db")
        module_id, task_id = _setup_eval_scenario(db_path)
        _apply_eval(db_path, task_id, module_id, "OK answer", 7.0, "Acceptable")

        conn = sqlite3.connect(db_path)
        status = conn.execute(
            "SELECT status FROM modules WHERE id = ?", (module_id,)
        ).fetchone()[0]
        completed = conn.execute(
            "SELECT completed FROM modules WHERE id = ?", (module_id,)
        ).fetchone()[0]
        conn.close()

        assert status == "completed", f"Score 7.0 should complete, got '{status}'"
        assert completed is not None, "Score 7.0 should set completed timestamp"

    def test_boundary_score_6_9_keeps_in_progress(self, tmp_path):
        """Score of 6.9 triggers 'in_progress' status (boundary test)."""
        db_path = str(tmp_path / "test.db")
        module_id, task_id = _setup_eval_scenario(db_path)
        _apply_eval(db_path, task_id, module_id, "Almost there", 6.9, "Close")

        conn = sqlite3.connect(db_path)
        status = conn.execute(
            "SELECT status FROM modules WHERE id = ?", (module_id,)
        ).fetchone()[0]
        completed = conn.execute(
            "SELECT completed FROM modules WHERE id = ?", (module_id,)
        ).fetchone()[0]
        conn.close()

        assert status == "in_progress", f"Score 6.9 should not complete, got '{status}'"
        assert completed is None, "Score 6.9 should not set completed timestamp"
