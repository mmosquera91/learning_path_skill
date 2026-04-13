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

### 3. Check for existing pending task
```sql
SELECT id FROM daily_tasks WHERE awaiting_response = 1;
```

If exists: skip (don't create duplicate)

### 4. Find next module to work on
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

### 5. Get resources for the module
```sql
SELECT url, title, type FROM resources WHERE module_id = ?;
```

### 6. Generate daily task content
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

### 7. Save task to database
```sql
INSERT INTO daily_tasks (module_id, date, content, awaiting_response)
VALUES (?, date('now'), ?, 1);
```

Get the task ID and save to config:
```sql
UPDATE config SET value=? WHERE key='pending_task_id';
```

### 8. Send to user via Telegram
```
📚 Tarea del día — {module_title}

{task_content}

Responde con /submit <tu respuesta>
```

## Quiet Hours
Do NOT send messages between 00:00-08:00. If cron triggers during this window, queue for 09:00.
