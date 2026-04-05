# Subskill: Init — Generate and Activate a Learning Path

## Trigger
User sends: `/tutor init <topic>` or "quiero aprender <topic>"

## Steps

### 0. Ensure database exists
```bash
python3 ~/.hermes/skills/tutor/scripts/init_db.py
```
This is idempotent — safe to run every time. It creates the DB if missing, skips if already initialized.

### 1. Check for existing active path
```bash
python3 -c "
import sqlite3, os
db = os.path.expanduser('~/.hermes/skills/tutor/learning.db')
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

### 2. Research phase — gather real resources
Before generating the syllabus, research the topic to find real, specific learning resources. Use `delegate_task` with `web_search`:

**Search strategy (run in parallel if possible):**
1. `"{topic} course syllabus modules curriculum"` — find typical module structure
2. `"{topic} lessons tutorial site:coursera.org OR site:edx.org OR site:khanacademy.org OR site:freecodecamp.org"` — find specific lesson URLs
3. `"{topic} tutorial beginner site:youtube.com"` — find specific video URLs (check channel credibility)
4. `"{topic} exercises practice problems"` — find interactive exercises
5. `"{topic} documentation official guide"` — find official docs

**For each result, capture:**
- Exact URL (must include specific path, not just homepage)
- Title of the lesson/course/module from the search result
- Source domain (prioritize trusted domains per rules below)

**TRUSTED SOURCE RULES (strictly enforce):**

**TIER SYSTEM (prioritize by reliability):**
- **TIER 1 (⭐⭐⭐⭐⭐):** chess.com/lessons/*, lichess.org/learn/*, lichess.org/practice/* — ALWAYS prioritize these, minimum 50% of resources
- **TIER 2 (⭐⭐⭐⭐):** coursera.org, edx.org, khanacademy.org, official documentation — max 2 per module
- **TIER 3 (⭐⭐):** YouTube single videos ONLY — max 1 per module, NO PLAYLISTS
- **TIER 4 (⭐⭐):** Reference materials — max 1 per module

**CRITICAL URL RULES:**
1. **NO YOUTUBE PLAYLISTS:** Reject ANY URL with `&list=` or `playlist?` — these break when videos change
2. **URLs MUST be specific** — reject generic paths
3. For chess.com: valid patterns are `chess.com/lessons/<lesson-slug>` only
4. For lichess: valid patterns are `lichess.org/learn#/<number>` or `lichess.org/practice/<category>/<slug>`
5. Do NOT fabricate URLs — only use URLs from search results
6. Do NOT use personal blogs or unknown domains

Store the research results in a structured format for the next step.

### 3. Generate the syllabus
Use the LLM to generate a structured learning path, **incorporating the research results from Step 2**. 

**CRITICAL: Follow TIER system when selecting resources:**
- TIER 1 (⭐⭐⭐⭐⭐): chess.com/lessons/*, lichess.org/learn/*, lichess.org/practice/* — MINIMUM 50% of resources
- TIER 2 (⭐⭐⭐⭐): coursera, edx, khanacademy, official docs — max 2 per module
- TIER 3 (⭐⭐): YouTube SINGLE VIDEOS only — max 1 per module
- NEVER include YouTube playlists (URLs with `&list=`)

Prompt:
```
Generate a structured learning syllabus for: {topic}

Use the following research results to build the syllabus. These are REAL resources found on the web:
---
{research_results}
---

Requirements:
- 8-15 modules, ordered from foundational to advanced
- Each module has: title, description (2-3 sentences), estimated time to complete
- Include 3-4 resources per module, selected ONLY from the research results above
- PRIORITY ORDER for resource selection (follow strictly):
  1. chess.com/lessons/<specific-lesson> (TIER 1 - most preferred)
  2. lichess.org/learn#/<number> or lichess.org/practice/<category> (TIER 1)
  3. coursera.org/learn/*, edx.org/learn/*, khanacademy.org/* (TIER 2)
  4. YouTube single videos ONLY if no better option (TIER 3)
- REJECT: YouTube playlists (any URL with &list= parameter)
- REJECT: Generic homepage URLs
- Each resource MUST use the exact URL from research
- Resource types: doc, video, exercise, article
- Mark 3-4 milestones (key checkpoint modules)
- Estimate total duration in weeks
- Language: match the user's language

TIER BALANCE CHECK: Each module must have at least 50% TIER 1 resources.

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
```

### 4. Validate resources

**STEP 4A: Run validation script**
Save syllabus to temp file and run validator:
```bash
python3 ~/.hermes/skills/tutor/scripts/validate_urls.py --http < /tmp/syllabus.json
```

This checks:
- URL pattern matches trusted sources (TIER 1-4)
- NO YouTube playlists (rejects `&list=`)
- HTTP status for TIER 1-2 URLs
- Balance: min 50% TIER 1 per module

**STEP 4B: Review validation output**
The script outputs:
```
TIER 1 (⭐⭐⭐⭐⭐ Interactive): 24
TIER 2 (⭐⭐⭐⭐ Official): 8
TIER 3 (⭐⭐ YouTube): 4
INVALID: 2

✅ Module Name (TIER 1: 60%)
❌ Bad Module (TIER 1: 25%) — Needs more interactive resources
   ❌ INVALID: https://youtube.com/playlist?...
      Reason: YouTube PLAYLIST - not allowed
```

**STEP 4C: Fix or regenerate**
- If INVALID URLs found: Remove them or find alternatives
- If TIER 1 < 50%: Add more interactive platform resources
- If YouTube playlists found: Replace with single video URLs
- Re-run validation until all modules pass

**Quick URL check (single URL):**
```bash
python3 ~/.hermes/skills/tutor/scripts/validate_urls.py --check "https://..."
```

### 5. Present syllabus for review
Format the syllabus using templates/syllabus.md and send to the user via Telegram.

For each module, render its study sources using the format defined in the template:
- Show the resource title as a clickable link
- Show the resource type (doc, video, exercise, article)
- Show ✅ for verified URLs or ⚠️ for unverified ones

This ensures the user can review BOTH the structure of the path AND the specific sources before confirming.

If there are unverified resources, add a note at the end:
```
⚠️ Estas fuentes no pudieron verificarse automáticamente:
{unverified_list}
Puedes continuar igual — las fuentes son complementarias y puedes reemplazarlas con /tutor edit.
```

### 6. Wait for user confirmation
- User sends `/tutor confirm` → proceed to step 7
- User sends `/tutor edit <feedback>` → regenerate syllabus incorporating feedback, go back to step 5
- If user is silent for 24h, the unconfirmed path auto-stays as draft

### 7. Save to SQLite and activate
```python
import sqlite3, os, json
from datetime import datetime, timezone

db = os.path.expanduser('~/.hermes/skills/tutor/learning.db')
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

### 8. Create cron jobs (if they don't exist)
Before creating cron jobs, check existing ones to avoid duplicates:

```python
# Use cronjob(action="list") to check for existing jobs
# Look for jobs with names: "tutor-daily" and "tutor-weekly"
# If a job with matching name already exists → skip it, do NOT create a duplicate
# If no matching name found → create it using cronjob(action="create")
```

Rules:
- **Always check by name** (`tutor-daily`, `tutor-weekly`) before creating.
- If a cron with that name exists (even if paused or with different schedule), do NOT create another.
- Only create missing cron jobs. Report which ones already existed vs. were created.

Daily cron: schedule `0 9 * * *`, deliver `telegram`, skill `tutor`
Weekly cron: schedule `0 22 * * 0`, deliver `telegram`, skill `tutor`

The prompt for each must contain the FULL content of the corresponding subskill (`daily.md` or `adapt.md`) inlined — cron sessions have zero context.

### 9. Send confirmation message
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
