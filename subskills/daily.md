# Subskill: Daily Task Generation

## Context
This subskill runs either:
- Automatically via cron job at 9:00 AM
- On demand when user asks for "today's task"

## Steps (follow this exact order)

### 1. Load skill and open DB
```bash
python3 -c "
import sqlite3, os, json
from datetime import datetime, timezone, timedelta

db = os.path.expanduser('~/.hermes/skills/tutor/learning.db')
conn = sqlite3.connect(db)
conn.execute('PRAGMA foreign_keys=ON')
c = conn.cursor()
"
```

### 2. Check for active path
```sql
SELECT value FROM config WHERE key='active_path_id';
```
If empty or no result → send to Telegram:
"No hay ningún learning path activo. Usa /tutor init [tema] para empezar."
→ END.

If path exists but status='paused' → END silently (don't send anything).

### 3. Check if task already sent today
```sql
SELECT value FROM config WHERE key='last_task_date';
```
If value = today's date → END silently (already sent today).

### 4. Check inactivity (based on last_response_date)
```sql
SELECT value FROM config WHERE key='last_response_date';
```
Calculate days since last response:
- 0 days (response today or yesterday) → proceed normally
- 1 day → proceed normally
- 2 days → send nudge: "👋 Haven't seen you in a couple days. Ready for today's task? Or /tutor skip if you're busy."
- 3 days → offer pause: "Looks like you've been busy this week. Want to /tutor pause and come back later?"
- 5+ days → auto-pause:
  ```sql
  UPDATE paths SET status='paused' WHERE id={active_path_id};
  UPDATE config SET value='' WHERE key='active_path_id';
  ```
  Send: "I've paused your learning path after {days} days of inactivity. Use /tutor resume when you're ready."
  → END.

### 5. Check for modules due for review (spaced repetition)
```sql
SELECT id, title, module_order, score_avg, times_repeated
FROM modules
WHERE path_id = {active_path_id}
  AND status = 'review'
  AND next_review_date <= date('now')
ORDER BY next_review_date ASC
LIMIT 1;
```
If found → this is today's module (review task).

### 6. Get current or next module
If no review due:
```sql
-- Check for module in progress
SELECT id, title, description, module_order
FROM modules
WHERE path_id = {active_path_id}
  AND status = 'in_progress'
LIMIT 1;
```

If no module in progress:
```sql
-- Get next pending module
SELECT id, title, description, module_order
FROM modules
WHERE path_id = {active_path_id}
  AND status = 'pending'
ORDER BY module_order ASC
LIMIT 1;
```

If neither → all modules completed:
```sql
-- Check if all are completed
SELECT COUNT(*) FROM modules WHERE path_id = {active_path_id} AND status != 'completed';
```
If 0 → send path completion message, set path status to 'completed'. → END.

### 7. Get resources for the module
```sql
SELECT url, title, type, verified FROM resources WHERE module_id = {module_id};
```

### 8. Generate the task
Use the LLM to create a focused daily task based on:
- Module title and description
- Module's current state (new, in_progress, or review)
- Past evaluations for this module (if review)
- Resources available

Prompt for task generation:
```
Generate a daily learning task for module: {module_title}
Description: {module_description}
Resources available: {resources}
This is a {new/review} module.

Requirements:
- Task should take 15-30 minutes
- Must be doable with the resources provided
- Include a clear deliverable (code snippet, explanation, diagram, etc.)
- If review: focus on areas where the student scored weakest previously
- Language: match the user's language (Spanish by default)
- Be encouraging but rigorous

Format the task with:
1. Brief context (2-3 sentences connecting to previous learning)
2. The task itself (clear, specific, actionable)
3. What to submit (what constitutes a "complete" answer)
4. 1-2 tips or hints (not solutions)
```

### 9. Save task to DB
```sql
INSERT INTO daily_tasks (module_id, date, content, awaiting_response, response_window_end)
VALUES ({module_id}, '{today}', '{task_content_escaped}', 1, '{window_end}');
```
Where `window_end` = now + 20 hours.

```sql
-- Update module status if new
UPDATE modules SET status = 'in_progress', started = '{now}' WHERE id = {module_id} AND status = 'pending';
```

```sql
-- Update config
UPDATE config SET value = '{today}' WHERE key = 'last_task_date';
UPDATE config SET value = '{task_id}' WHERE key = 'pending_task_id';
```

### 10. Send task via Telegram
Format using templates/daily-task.md and deliver.

### 11. Error handling
- DB error → send error details to Telegram: "⚠️ Error generating daily task: {error}"
- LLM error → retry once, then send fallback: "Technical issue with today's task. Try again in a few minutes or use /tutor status."
