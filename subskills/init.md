# Subskill: Init — Generate and Activate a Learning Path

## Trigger
User sends: `/tutor init <topic>` or "quiero aprender <topic>"

## Steps

### 1. Check for existing active path
```bash
python3 -c "
import sqlite3, os
db = os.path.expanduser('~/.hermes/skills/learning-path/learning.db')
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute('SELECT value FROM config WHERE key=\"active_path_id\"')
row = c.fetchone()
if row and row[0]:
    c.execute('SELECT topic, status FROM paths WHERE id=?', (row[0],))
    p = c.fetchone()
    print(f'ACTIVE_PATH: {p[0]} (status: {p[1]})')
else:
    print('NO_ACTIVE_PATH')
conn.close()
"
```
If there's already an active path, ask the user: "You already have an active path: {topic}. Do you want to /tutor pause it first and create a new one?"

### 2. Generate the syllabus
Use the LLM to generate a structured learning path. Prompt:

```
Generate a structured learning syllabus for: {topic}

Requirements:
- 8-15 modules, ordered from foundational to advanced
- Each module has: title, description (2-3 sentences), estimated time to complete
- Include 2-3 resources per module (real, well-known URLs when possible)
- Resource types: doc, video, exercise, article
- Mark 3-4 milestones (key checkpoint modules)
- Estimate total duration in weeks
- Language: match the user's language

Output as valid JSON:
{
  "topic": "...",
  "description": "...",
  "estimated_duration": "...",
  "modules": [
    {
      "title": "...",
      "description": "...",
      "estimated_time": "...",
      "resources": [
        {"url": "...", "title": "...", "type": "doc|video|exercise|article"}
      ],
      "is_milestone": false
    }
  ]
}

IMPORTANT: Only include real, well-known URLs. Do not fabricate links.
For each resource, prefer official documentation, established tutorials, or well-known platforms.
```

### 3. Validate resources (Fase 2+)
For each URL in the generated syllabus:
- Try a HEAD request using `terminal`: `curl -sI -o /dev/null -w "%{http_code}" --max-time 10 "<URL>"`
- If status 200-399: mark as `verified='ok'`
- If timeout or 404+: mark as `verified='unverified'`
- Collect list of unverified URLs

### 4. Present syllabus for review
Format the syllabus using templates/syllabus.md and send to the user via Telegram.

If there are unverified resources, add a note:
```
⚠️ These resources could not be verified:
{unverified_list}
You can proceed anyway — resources are supplementary.
```

### 5. Wait for user confirmation
- User sends `/confirm` → proceed to step 6
- User sends `/edit <feedback>` → regenerate syllabus incorporating feedback, go back to step 4
- If user is silent for 24h, the unconfirmed path auto-stays as draft

### 6. Save to SQLite and activate
```python
import sqlite3, os, json
from datetime import datetime, timezone

db = os.path.expanduser('~/.hermes/skills/learning-path/learning.db')
conn = sqlite3.connect(db)
conn.execute("PRAGMA foreign_keys=ON")
c = conn.cursor()

# Insert path
now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
c.execute('INSERT INTO paths (topic, status, is_active, confirmed, created) VALUES (?, ?, 1, 1, ?)',
          (syllabus["topic"], "active", now))
path_id = c.lastrowid

# Insert modules and resources
for i, mod in enumerate(syllabus["modules"]):
    c.execute('''INSERT INTO modules (path_id, title, description, module_order, status)
                 VALUES (?, ?, ?, ?, 'pending')''',
              (path_id, mod["title"], mod["description"], i+1))
    mod_id = c.lastrowid
    for res in mod.get("resources", []):
        c.execute('''INSERT INTO resources (module_id, url, title, type, verified)
                     VALUES (?, ?, ?, ?, ?)''',
                  (mod_id, res["url"], res["title"], res["type"], res.get("verified", "pending")))

# Set as active
c.execute('UPDATE config SET value=? WHERE key="active_path_id"', (str(path_id),))
conn.commit()
conn.close()
```

### 7. Send confirmation message
```
✅ Learning path activated: {topic}
📚 {N} modules loaded
🎯 First module: {first_module_title}
Type /tutor status anytime to check progress.
```

## Error Handling
- If LLM generates invalid JSON: retry once with explicit "return valid JSON only"
- If DB write fails: report error to user, do NOT leave partial state
- If init_db.py hasn't been run: run it first, then proceed
