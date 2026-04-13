# Subskill: Init — Generate and Activate a Learning Path

## Trigger
User sends: `/tutor init <topic>` or "quiero aprender <topic>"

## Steps

### 0. Ensure database exists
```bash
python3 ~/.hermes/skills/tutor/scripts/init_db.py
```
Idempotent — safe to run every time.

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
If active path exists, ask: "You already have an active path: {topic}. /tutor pause it first?"

## Resource Tier Reference (for cron context self-containment)

| Tier | Description | Examples | Limits |
|------|-------------|----------|--------|
| TIER 1 | Interactive platforms with exercises | exercism.org, codecademy.com, duolingo.com, chess.com/lessons | MIN 50% per module |
| TIER 2 | Official courses and docs | coursera.org, edx.org, khanacademy.org | Max 2/module |
| TIER 3 | YouTube single videos ONLY | youtube.com/watch?v=... | Max 1/module, NO PLAYLISTS |
| TIER 4 | Reference materials | wikipedia, github docs, medium | Max 1/module |

TIER RULES: See inline tier table above. Full rules in CONTRIBUTING.md §1-3.

### 2. Research phase — gather real resources
Use `delegate_task` with `web_search`:

1. `"{topic} course syllabus modules curriculum"`
2. `"{topic} lessons site:coursera.org OR site:edx.org OR site:khanacademy.org"`
3. `"{topic} tutorial beginner site:youtube.com"`
4. `"{topic} exercises practice problems"`
5. `"{topic} documentation official guide"`

**For each result capture:** exact URL, title, source domain. NO fabricated URLs.

### 3. Generate the syllabus
Incorporate research results from Step 2. Prompt the LLM with:
```
Generate a JSON syllabus for {topic} using the research results above.

Requirements:
- 8-15 modules, foundational → advanced, each with title/description/estimated_time
- 3-4 resources per module from research results ONLY
- PRIORITY: TIER 1 > TIER 2 > TIER 3 > TIER 4
- REJECT: YouTube playlists (&list=), generic homepage URLs
- 3-4 milestones, estimate total duration in weeks
- Match user's language

JSON schema:
{"topic":"...","description":"...","estimated_duration":"...","modules":[{"title":"...","description":"...","estimated_time":"...","resources":[{"url":"...","title":"...","type":"doc|video|exercise|article"}],"is_milestone":false}]}
```

Save to `/tmp/syllabus.json`. Render using templates/init-syllabus.md:
```bash
python3 -c "import json; d=json.load(open('/tmp/syllabus.json')); t=open('templates/init-syllabus.md').read(); [t:=t.replace('{{'+k+'}}', str(v)) for k in ['topic','description','estimated_duration']]; mods=''; [(mods:=mods+f\"### {m['title']} 🎯\n\n{m['description']}\n\n**Tiempo:** {m['estimated_time']}\n\n\"+''.join(f\"- [{r['title']}]({r['url']}) ({r['type']}) ✅\n\" for r in m.get('resources',[]))+\"\n---\n\n\") for m in d.get('modules',[])]; t=t.replace('{{#modules}}',mods).replace('{{/modules}}',''); print(t)"
```

Display the rendered syllabus to the user.

### 4. Validate resources
```bash
python3 ~/.hermes/skills/tutor/scripts/validate_urls.py --http < /tmp/syllabus.json
```
- NO YouTube playlists (`&list=` or `playlist?` — REJECTED)
- TIER 1 minimum 50% per module
- Single URL check: `validate_urls.py --check "https://..."`

If INVALID or TIER 1 < 50%: fix and re-validate.

### 5. Present syllabus for review
The rendered syllabus from Step 3 is sent to user via Telegram.

If unverified resources: add ⚠️ warning with list.

### 6. Wait for user confirmation
- `/tutor confirm` → step 7
- `/tutor edit <feedback>` → regenerate, back to step 3
- Silent 24h → stays as draft

### 7. Save to SQLite and activate
```bash
python3 scripts/save_path.py --file /tmp/syllabus.json
```

### 8. Create cron jobs (if they don't exist)
Check by name (`tutor-daily`, `tutor-weekly`) via `cronjob(action="list")`. If missing, create:
- Daily: `0 9 * * *` | Weekly: `0 22 * * 0`
- Both: deliver `telegram`, skill `tutor`
- Inline full subskill content (`daily.md` or `adapt.md`) — cron has zero context.

### 9. Send confirmation message
```
✅ Learning path activated: {topic}
📚 {N} modules loaded
🎯 First module: {first_module_title}
Type /tutor status anytime to check progress.
```

## Error Handling
- Invalid JSON from LLM: retry once with "return valid JSON only"
- DB write fails: report error, do NOT leave partial state
- init_db.py not run: run it first, then proceed
