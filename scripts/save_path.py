#!/usr/bin/env python3
"""
Save syllabus JSON to SQLite database.
Usage: python3 scripts/save_path.py --file /tmp/syllabus.json
       cat /tmp/syllabus.json | python3 scripts/save_path.py
"""
import sqlite3
import os
import json
import sys
import argparse
from datetime import datetime, timezone

DB_PATH = os.path.expanduser("~/.hermes/skills/tutor/learning.db")

def save_syllabus(syllabus_data):
    """Insert syllabus JSON into SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    c = conn.cursor()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Insert path
    c.execute(
        "INSERT INTO paths (topic, status, is_active, confirmed, created) VALUES (?, ?, 1, 1, ?)",
        (syllabus_data["topic"], "active", now)
    )
    path_id = c.lastrowid

    # Insert modules and resources
    for i, mod in enumerate(syllabus_data.get("modules", []), start=1):
        c.execute(
            "INSERT INTO modules (path_id, title, description, module_order, status) VALUES (?, ?, ?, ?, 'pending')",
            (path_id, mod["title"], mod["description"], i)
        )
        mod_id = c.lastrowid
        for res in mod.get("resources", []):
            c.execute(
                "INSERT INTO resources (module_id, url, title, type, verified) VALUES (?, ?, ?, ?, ?)",
                (mod_id, res["url"], res["title"], res["type"], res.get("verified", "pending"))
            )

    # Set as active path
    c.execute("UPDATE config SET value=? WHERE key='active_path_id'", (str(path_id),))

    conn.commit()
    conn.close()
    return path_id

def main():
    parser = argparse.ArgumentParser(description="Save syllabus JSON to database")
    parser.add_argument("--file", "-f", help="Path to syllabus JSON file")
    args = parser.parse_args()

    try:
        if args.file:
            with open(args.file) as f:
                syllabus_data = json.load(f)
        else:
            syllabus_data = json.load(sys.stdin)

        path_id = save_syllabus(syllabus_data)
        print(f"SUCCESS: Path {path_id} created and activated")
        sys.exit(0)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except sqlite3.Error as e:
        print(f"ERROR: Database error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
