# Evaluation Rubric

## Scoring Criteria

Each evaluation produces TWO scores on a 1-10 scale:

### 1. Conceptual Comprehension (CC)
- 1-3: Cannot explain the core concept in their own words
- 4-5: Partial understanding, significant gaps or misconceptions
- 6-7: Solid understanding, minor gaps
- 8-9: Deep understanding, can explain edge cases and trade-offs
- 10: Expert-level, connects to broader concepts outside the module

### 2. Application Ability (AA)
- 1-3: Cannot apply the concept even with guidance
- 4-5: Can apply with substantial help or examples
- 6-7: Can apply independently to standard problems
- 8-9: Can apply to novel/unfamiliar problems
- 10: Can teach others and optimize solutions

## Final Score
```
score = (CC + AA) / 2
```

## Decision Rules
- score >= 7.0 → ADVANCE to next module
- score 4.0-6.9 → REPEAT module with clarification on weak areas
- score < 4.0 → DECOMPOSE module into smaller sub-modules

## Spaced Repetition Scheduling
- score >= 8.0 → next_review_date = today + 7 days
- score 5.0-7.9 → next_review_date = today + 3 days
- score < 5.0 → next_review_date = next session (tomorrow)

## Output Format (JSON)
```json
{
  "conceptual_comprehension": <1-10>,
  "application_ability": <1-10>,
  "score": <average>,
  "decision": "<advance|repeat|decompose>",
  "feedback": "<specific feedback, 2-4 sentences>",
  "strengths": ["<what they did well>"],
  "improvements": ["<what needs work>"],
  "next_review_days": <1|3|7>
}
```

## Rules
- NEVER give a score without citing specific evidence from the response
- Feedback must be actionable, not generic ("good job" is not feedback)
- If the response is too short to evaluate properly, ask for elaboration instead of giving a low score
- Always respond in the user's language
- **Proportional scoring:** Don't penalize heavily for a single minor conceptual imprecision when all practical application is correct. A wrong term in an explanatory note should cost 0.5-1 point, not 3+. Score Application (what they can DO) independently from Comprehension (how they explain it). If code runs perfectly and tasks are completed, Application should be 7+ minimum.
