# Subskill: Adapt — Adapt Learning Path

## Trigger
- `/tutor review <module>` — repeat a completed module
- Weekly cron job for adaptation

## Steps

### 1. For /tutor review command
Note: The user input parameter must be escaped before binding:
- Replace `\` with `\\`
- Replace `%` with `\%`
- Replace `_` with `\_`
- Wrap in `%...%` for substring matching
- Bind the escaped string as the parameter

```sql
SELECT id, title, status FROM modules
WHERE path_id = (SELECT value FROM config WHERE key='active_path_id')
AND title LIKE ? ESCAPE '\'
ORDER BY module_order;
```

If found and status = 'completed':
```sql
UPDATE modules
SET status = 'pending',
    times_repeated = times_repeated + 1,
    completed = NULL
WHERE id = ?;
```

Send: "🔄 Módulo marcado para revisión: {title}. Aparecerá en tu próxima tarea."

### 2. Weekly adaptation analysis
Run every Sunday at 22:00 via cron.

Query performance data:
```sql
SELECT 
    m.title,
    m.score_avg,
    m.times_repeated,
    COUNT(t.id) as task_count,
    AVG(t.score) as avg_task_score
FROM modules m
LEFT JOIN daily_tasks t ON m.id = t.module_id
WHERE m.path_id = (SELECT value FROM config WHERE key='active_path_id')
GROUP BY m.id;
```

### 3. Adaptation rules
- If avg score < 5 for a module: suggest review
- If multiple modules have low scores: slow down pace
- If all scores > 8: can accelerate
- If streak broken: send encouragement

### 4. Send weekly report
```
📈 Resumen semanal de aprendizaje

Módulos completados esta semana: {count}
Puntuación promedio: {avg}
Racha actual: {streak} días

{{#struggling}}
📚 Recomendación: Repasa {module_title} — los ejercicios adicionales ayudarán.
{{/struggling}}

{{#doing_well}}
🎉 ¡Excelente progreso! Estás listo para el siguiente módulo.
{{/doing_well}}
```
