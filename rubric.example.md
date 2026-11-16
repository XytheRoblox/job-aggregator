# Job Score Rubric

> **Template:** copy this file to `rubric.md` and edit it. The weights below are a starting point. Change them to match what matters most to you, but keep the total at 100.

The agent follows this rubric to give each job posting a **Job Score** from 0 to 100, using your preferences in `profile.yaml`.

## 1. Criteria

| Criterion | Weight | How to judge it |
|---|---|---|
| Title and seniority fit | 25 | Compare the job title and level to `target_titles` and `seniority_levels`. |
| Industry or lane fit | 20 | Compare the company's industry and the team's focus to `industries_or_lanes`. |
| Location fit | 20 | Compare the job's work mode to `locations.ranked` and use the **highest-ranked entry it matches**: 1st = 20, 2nd = 18, 3rd = 15, 4th = 10, 5th or later = 6, no match = 0. A job that matches nothing still gets scored, with 0 here. See "Location rules" below. |
| Compensation | 20 | Compare the posted pay to `comp_floor_usd`. Full points if the whole range is at or above the floor; fewer if only the top of the range reaches it. |
| Must-haves and company signals | 15 | Score only the `must_haves` the posting confirms (count for) or contradicts (count against), plus any signs about the company's health or culture it states. List a must-have the posting doesn't mention as unknown; it doesn't affect points. If the posting mentions no must-haves and no company signals, the whole criterion is unknown. |
| **Total** | **100** | |

**Awarding points:** give each criterion anywhere from 0 up to its weight. Give full points for a clear match, about half for a partial match, and 0 for a clear mismatch. Location fit is the exception: it uses only the fixed points by rank above.

### Location rules

- **Excluded jobs are hidden:** a job that matches any entry in `locations.exclude` is hidden, not scored. It doesn't appear in results or on the dashboard.
- **Remote jobs restricted to another country:** a remote job that requires living outside the US counts as **on-site outside the US**, both for ranking and for exclusion.
- **Remote region unclear:** if a remote job doesn't make clear where you may live, don't exclude it. Score it as remote, using the highest-ranked remote entry, and add the note **"remote region unclear"**.
- **Work mode unknown:** if the posting doesn't say whether the job is remote, hybrid or on-site, or where, Location fit is **unknown**.

## 2. Unknown information

- If the posting doesn't say enough to judge a criterion, mark it **unknown**. **Never guess.**
- Leave unknown criteria out and rescale the rest to 100:
  `Job Score = (points earned ÷ total weight of the known criteria) × 100`, rounded to a whole number (.5 rounds up).
- Report how many of the 5 criteria were known (for example, "4 of 5").
- If all 5 are unknown, don't give a score. Report "not enough information".
- **Empty profile fields:** if a field in `profile.yaml` that a criterion needs for this posting is empty, mark that criterion **unknown** too. For example, any job with `locations.ranked` empty, or any pay with `comp_floor_usd` empty. If `locations.exclude` is empty, no jobs are hidden. If `must_haves` is empty, judge that criterion on company signals alone. If `needs_visa_sponsorship` or `dealbreakers` is empty, that override doesn't apply.

*Example:* the posting lists no pay, so Compensation is unknown. The other four criteria are worth 80 in total. If they earn 60 points, the Job Score is 60 ÷ 80 × 100 = **75**.

## 3. Hard overrides

These change the recommendation to **Skip** no matter what the score is. They **never change the score itself.**

- **(a) Dealbreaker:** the posting matches anything in `dealbreakers`.
- **(b) Visa sponsorship:** `needs_visa_sponsorship` is true and the posting says it doesn't sponsor visas.

**Note, not an override:** if `needs_visa_sponsorship` is true and the posting doesn't mention sponsorship at all, add the note **"sponsorship not mentioned"**, but don't Skip because of it.

## 4. Recommendation

| Job Score | Recommendation |
|---|---|
| 75 to 100 | **Strong** |
| 50 to 74 | **Maybe** |
| Under 50 | **Skip** |

If a hard override applies, the recommendation is **Skip** whatever the score says.

## 5. Output format

Report every job in this format:

```
Job Score: 85
Criteria known: 4 of 5
Work mode: Hybrid, Austin, TX

- Title and seniority fit: 25/25. "Senior Product Manager" matches a target title and level.
- Industry or lane fit: 10/20. Fintech company, but the role is on "internal HR tools".
- Location fit: 18/20. "Hybrid, 3 days a week in our Austin office" matches your 2nd choice, "Austin, TX (hybrid or on-site)".
- Compensation: unknown. The posting lists no salary.
- Must-haves and company signals: 15/15. Confirms "health insurance". Clear path to promotion: unknown (not mentioned).

Overrides: none
Notes: none

Recommendation: Strong
```

The note "sponsorship not mentioned" appears only when `needs_visa_sponsorship` is true in `profile.yaml`. The note "remote region unclear" appears only for remote jobs whose allowed region isn't clear.

*Sample math:* 25 + 10 + 18 + 15 = 68 points out of the 80 known, so 68 ÷ 80 × 100 = **85**.

- Quote the posting in the reasons wherever you can.
- Write `Overrides: none` and `Notes: none` when there aren't any.
