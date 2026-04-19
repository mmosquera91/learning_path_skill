# Subskill: Daily — Generate Daily Task

## Trigger
Cron job: `0 9 * * *` (9 AM daily)

## Resource Tier Reference (for cron context)

| Tier | Source Type | Examples | Reliability | Max/Module |
|------|-------------|----------|-------------|------------|
| TIER 1 | Interactive platforms | exercism.org, codecademy.com, duolingo.com, chess.com/lessons | ⭐⭐⭐⭐⭐ | Unlimited |
| TIER 2 | Official courses | Coursera, edX, Khan Academy, docs | ⭐⭐⭐⭐ | 2 |
| TIER 3 | YouTube (single videos ONLY) | Individual videos, NO playlists | ⭐⭐ | 1 |
| TIER 4 | Reference materials | Wikipedia, technical blogs | ⭐⭐ | 1 |

## Steps

### 1. Ensure database exists
```bash
python3 ~/.hermes/skills/tutor/scripts/init_db.py
```

### 2. Check for active path
```sql
SELECT value FROM config WHERE key='active_path_id';
```

If no active path: **END IMMEDIATELY — NO OUTPUT, NO MESSAGE**
- Do NOT send any message to Telegram
- Do NOT generate any response
- Exit with empty output (user hasn't started a path yet)

### 3. Check for path paused status
```sql
SELECT status FROM paths WHERE id = (SELECT value FROM config WHERE key='active_path_id');
```
If status = 'paused': **END SILENTLY** — path was manually or auto-paused, do not send any message.

### 4. Check for existing pending task
```sql
SELECT id FROM daily_tasks WHERE awaiting_response = 1;
```

If exists: skip (don't create duplicate)

### 5. Check inactivity and auto-pause
```sql
SELECT value FROM config WHERE key='last_response_date';
```
Calculate days since last response using `julianday('now') - julianday(value)`:
- **2 days:** Send nudge (in user's locale):
  - locale=es: "👋 Llevas un par de días sin actividad. ¿Listo para la tarea de hoy? O /tutor skip si estás ocupado."
  - locale=en: "👋 You haven't been active for a couple of days. Ready for today's task? Or /tutor skip if you're busy."
- **3 days:** Send offer to pause (in user's locale):
  - locale=es: "Parece que has estado ocupado. ¿Quieres /tutor pause y volver después?"
  - locale=en: "You seem to have been busy. Want to /tutor pause and come back later?"
- **5+ days:** Auto-pause and notify:
  ```sql
  UPDATE paths SET status='paused', is_active=0 WHERE id = (SELECT value FROM config WHERE key='active_path_id');
  UPDATE config SET value='' WHERE key='active_path_id';
  ```
  Send (in user's locale):
  - locale=es: "He pausado tu learning path tras {days} días de inactividad. Usa /tutor resume cuando estés listo."
  - locale=en: "I've paused your learning path after {days} days of inactivity. Use /tutor resume when you're ready."
  **END** — do not send a task

### 6. Find next module to work on
```sql
SELECT id, title, description, module_order
FROM modules
WHERE path_id = (SELECT value FROM config WHERE key='active_path_id')
AND status IN ('pending', 'in_progress')
ORDER BY module_order
LIMIT 1;
```

If no pending modules: path is complete!
```sql
UPDATE paths SET status='completed', completed=datetime('now')
WHERE id = (SELECT value FROM config WHERE key='active_path_id');
```
Send: "🎉 ¡Felicitaciones! Has completado tu plan de aprendizaje. Usa /tutor init para comenzar uno nuevo."

### 7. Get resources for the module
```sql
SELECT url, title, type FROM resources WHERE module_id = ?;
```

### 8. Generate daily task content
Use LLM to generate a specific, actionable task:

```
Create a daily learning task for:
Module: {module_title}
Description: {module_description}
Resources: {resources}

Requirements:
- One clear, specific task (15-30 minutes)
- Reference specific resources when relevant
- Ask for a response that demonstrates understanding
- Language: Spanish

Output format:
{
  "task": "Clear instruction text",
  "expected_response_type": "brief|detailed|exercise|reflection"
}
```

**Error handling:**
```python
try:
    # LLM task generation (Step 8)
    # If LLM fails or returns invalid JSON:
    #   - Retry once with: "Output valid JSON only, no markdown, no explanation"
    #   - If retry fails: report error in user's language (check config.locale):
#     - locale=es or not set: "No pude generar la tarea. Intenta de nuevo mas tarde."
#     - locale=en: "I could not generate the task. Please try again later."
except Exception:
    # Report error to user, do NOT write to DB or send Telegram
```

### 9. Save task to database
```sql
INSERT INTO daily_tasks (module_id, date, content, awaiting_response)
VALUES (?, date('now'), ?, 1);
```

Get the task ID and save to config:
```sql
UPDATE config SET value=? WHERE key='pending_task_id';
```

**Error handling:**
```python
try:
    # Database write (Step 9)
    # If sqlite3.OperationalError or other DB error:
    #   - Report error in user's language (check config.locale):
#     - locale=es or not set: "Error al guardar la tarea. Intenta de nuevo mas tarde."
#     - locale=en: "Failed to save the task. Please try again later."
    #   - Do NOT send Telegram if DB write fails
    #   - Do NOT leave partial state
except sqlite3.OperationalError:
    # Rollback if needed, report error, do NOT leave partial state
```

### 10. Send to user via Telegram
```
📚 Tarea del día — {module_title}

{task_content}

Responde con /submit <tu respuesta>
```

**Error handling:**
```python
try:
    # Telegram delivery (Step 10)
    # If Hermes deliver fails:
    #   - Report error in user's language (check config.locale):
#     - locale=es or not set: "No pude enviar la tarea. Intentare de nuevo manana."
#     - locale=en: "I could not send the task. I will try again tomorrow."
    #   - Do NOT mark task as sent if delivery fails
except Exception:
    # Report error to user, retry tomorrow
```

## Quiet Hours
Do NOT send messages between 00:00-08:00. If cron triggers during this window, queue for 09:00.
