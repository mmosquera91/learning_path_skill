# Subskill: Eval — Evaluate Task Submission

## Trigger
User sends: `/submit <response>` or confirms free-text as submission

## Steps

### 1. Retrieve the pending task
```sql
SELECT t.id, t.module_id, t.content, t.date, m.title, m.path_id
FROM daily_tasks t
JOIN modules m ON t.module_id = m.id
WHERE t.awaiting_response = 1
ORDER BY t.date DESC LIMIT 1;
```

If no pending task, report in user's language (check config.locale):
- locale=es or not set: "No hay tarea pendiente. Usa /tutor status para ver tu progreso."
- locale=en: "No pending task. Use /tutor status to check your progress."

### 2. Evaluate the submission
Prompt the LLM to evaluate:

```
Evaluate this learning task submission.

Task: {task_content}
Submission: {user_response}
Module: {module_title}

Evaluate on:
1. Completeness (did they address all parts?)
2. Understanding (do they grasp the concepts?)
3. Effort (genuine attempt vs minimal response)

Score: 1-10
Provide specific, constructive feedback.
```

### 3. Save evaluation
```sql
UPDATE daily_tasks
SET response = ?,
    score = ?,
    feedback = ?,
    awaiting_response = 0
WHERE id = ?;
```

### 4. Update module progress
```sql
-- Calculate average score for this module
SELECT AVG(score) FROM daily_tasks
WHERE module_id = ? AND score IS NOT NULL;

-- Update module
UPDATE modules
SET score_avg = ?,
    status = CASE WHEN ? >= 7 THEN 'completed' ELSE 'in_progress' END,
    completed = CASE WHEN ? >= 7 THEN datetime('now') ELSE NULL END
WHERE id = ?;
```

### 5. Check for module completion
If score >= 7:
- Mark module as completed
- Update streak count in config
- Send completion message in user's language (check config.locale):
  - locale=es or not set: "✅ Módulo completado: {module_title}"
  - locale=en: "✅ Module completed: {module_title}"

If score < 7:
- Increment times_repeated
- Send keep-practicing message in user's language (check config.locale):
  - locale=es or not set: "📚 Sigue practicando. Revisarás este módulo mañana."
  - locale=en: "📚 Keep practicing. You will review this module tomorrow."

### 6. Send feedback
```
📊 Evaluación del {{date}}

Puntuación: {{score}}/10

{{feedback}}

{{#completed}}
✅ {{#es}}¡Módulo completado!{{/es}}{{#en}}Module completed!{{/en}}
{{/completed}}
{{^completed}}
📚 {{#es}}Revisaremos este tema mañana.{{/es}}{{#en}}We will review this topic tomorrow.{{/en}}
{{/completed}}
```

## Error Handling
- If DB update fails: rollback and report error
- If evaluation prompt fails: use generic encouraging feedback
