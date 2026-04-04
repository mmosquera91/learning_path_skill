# Subskill: Adapt — Weekly Review and Path Adjustment

## Trigger
- Cron job: Sundays at 22:00
- Manual: /tutor review [module]

## Steps for Weekly Review

### 1. Open DB and get active path
```sql
SELECT value FROM config WHERE key='active_path_id';
```
If empty → END silently.

```sql
SELECT id, topic, status, created FROM paths WHERE id = {active_path_id};
```

### 2. Calculate weekly metrics (last 7 days)
```sql
-- Tasks sent
SELECT COUNT(*) FROM daily_tasks
WHERE module_id IN (SELECT id FROM modules WHERE path_id = {active_path_id})
  AND date >= date('now', '-7 days');

-- Tasks completed (has response)
SELECT COUNT(*) FROM daily_tasks
WHERE module_id IN (SELECT id FROM modules WHERE path_id = {active_path_id})
  AND date >= date('now', '-7 days')
  AND response IS NOT NULL;

-- Tasks skipped
SELECT COUNT(*) FROM daily_tasks
WHERE module_id IN (SELECT id FROM modules WHERE path_id = {active_path_id})
  AND date >= date('now', '-7 days')
  AND skipped = 1;

-- Average score
SELECT AVG(score) FROM daily_tasks
WHERE module_id IN (SELECT id FROM modules WHERE path_id = {active_path_id})
  AND date >= date('now', '-7 days')
  AND score IS NOT NULL;

-- Modules completed this week
SELECT COUNT(*) FROM modules
WHERE path_id = {active_path_id}
  AND status = 'completed'
  AND completed >= date('now', '-7 days');

-- Days inactive
SELECT julianday('now') - julianday(value) FROM config WHERE key='last_response_date';
```

### 3. Calculate streak
```sql
-- Count consecutive days with responses ending at most yesterday
SELECT date, awaiting_response, skipped
FROM daily_tasks
WHERE module_id IN (SELECT id FROM modules WHERE path_id = {active_path_id})
ORDER BY date DESC
LIMIT 14;
```
Walk backwards counting consecutive days where response is not null and not skipped.

### 4. Apply adaptation logic

**Rule 1: >50% tasks skipped this week**
→ Recommend reducing frequency or changing topic.
Message: "This week you skipped {skip_pct}% of tasks. Options: /tutor pause to take a break, or /tutor switch to try a different topic."

**Rule 2: Average score < 5.0 in current module**
→ Flag for decomposition next session.
```sql
UPDATE modules SET next_review_date = date('now', '+1 day') WHERE id = {current_module_id};
```

**Rule 3: Average score > 8.0 over last 3 completed modules**
→ Offer acceleration.
Message: "📈 Your last 3 modules averaged {avg}/10. Consider: /tutor accelerate to skip foundational content."

**Rule 4: 3+ days inactive**
→ Already handled by daily cron (nudge/pause), but mention in report.

### 5. Get module status overview
```sql
SELECT title, status, score_avg, module_order
FROM modules
WHERE path_id = {active_path_id}
ORDER BY module_order;
```

### 6. Generate next week preview
Look at the current module and the next 1-2 pending modules:
```sql
SELECT title, description FROM modules
WHERE path_id = {active_path_id}
  AND status IN ('in_progress', 'pending')
ORDER BY module_order
LIMIT 3;
```

### 7. Format and send report
Use templates/weekly-report.md.

### 8. Save to Obsidian (if vault configured)
```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
WEEK=$(date +%Y-W%V)
mkdir -p "$VAULT/Learning/weekly"
cat > "$VAULT/Learning/weekly/$WEEK.md" << 'REPORT'
{full_report_markdown}
REPORT
```

If OBSIDIAN_VAULT_PATH not set, skip this step silently.

### 9. Update config
```sql
-- Increment weekly counter
UPDATE config SET value = CAST(CAST(value AS INTEGER) + 1 AS TEXT) WHERE key = 'weekly_count';
```

---

## Steps for Module Review (/tutor review <module>)

### 1. Find the module
```sql
SELECT id, title, description FROM modules
WHERE path_id = {active_path_id}
  AND title LIKE '%{module_query}%'
LIMIT 1;
```

### 2. Reset for review
```sql
UPDATE modules SET
  status = 'in_progress',
  next_review_date = NULL
WHERE id = {module_id};
```

### 3. Generate a review task focused on weak areas
Look at past evaluations for this module:
```sql
SELECT score, feedback FROM daily_tasks
WHERE module_id = {module_id} AND score IS NOT NULL
ORDER BY date DESC;
```

Generate review task targeting the weakest areas from past feedback.

### 4. Send the review task
Format as daily task.
