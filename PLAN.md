# Job Aggregator — Project Plan

## Vision

An open-source job aggregator for job seekers. It finds companies, collects
their open jobs from ATS feeds, matches those jobs against the user's
profile and resumes, and shows a daily dashboard of top matches (e.g. 9am,
top 3–5 to apply to). The user reviews and submits every application
themselves — this tool never applies on its own.

## Principles

- **Free core that works with no AI**: aggregation, filters, Fit Quotient,
  and the dashboard all work without calling any model.
- **Claude is an optional upgrade**: Job Score and application prep use the
  model, but the core pipeline doesn't depend on them.
- **Code for anything deterministic, the model only for judgment.**
- **Hosting-ready but not hosting-built**: the engine (`job_agent/`) is kept
  separate from the dashboard; data is tied to a user ID; paths are
  configurable — so this could run hosted for multiple users later, even
  though today it's built for one person running it locally.
- **Low cost, no terminal after install**, with the eventual goal of a
  double-click install.
- **Never auto-submit applications, create accounts, or solve CAPTCHAs.**

## Architecture

This is a **pipeline**, not a live web app with a database — it runs as
scheduled batch steps that write plain data files, and the dashboard just
reads the latest files. Think of it as an assembly line: each stage reads
what the previous stage produced and hands off a file to the next stage.

1. **Company Finder** (weekly) → builds/updates a watchlist of companies
   and which ATS each one uses.
2. **Job Finder** (daily) → pulls raw postings from each watched company's
   ATS feed, normalizes them into one standard job format, dedups, and
   diffs against the previous run (new/unchanged/edited/gone).
3. **Funnel** → cheap code filters first (location, keywords), then Fit
   Quotient (still code — resume/JD keyword overlap), narrowing to the
   top ~20 — only those go on to Job Score, where the model gets involved.
4. **Dashboard** → a thin local web app that only *reads* the latest
   output files and displays them; no pipeline logic lives there.
5. **Scheduler** (step 7) → triggers the daily run automatically.

**Where the model fits in**: `job_agent` will expose an **MCP server**
(step 3d) — the structured doorway Claude uses to call into the engine's
data and functions, instead of operating freeform. The model is only
invoked for the two judgment calls (Job Score, application prep); fetching,
filtering, and deduping stay pure deterministic code.

**Not yet decided** (to be settled at the matching roadmap step, not
guessed now):
- Storage format for job data (flat JSON files vs. SQLite) — step 4.
- Scheduler mechanism (macOS `launchd` vs. a simple loop) — step 7.
- Exact shape of the MCP server's tools — step 3d.

## Key decisions

- **Two-step discovery**: a weekly **Company Finder** followed by a daily
  **Job Finder**.
- **Sources, in order**: Greenhouse, Lever, and Ashby first; Workday later
  (unofficial, since it has no public API); VC portfolio pages, HN Who's
  Hiring, and YC for company discovery; LinkedIn last, as a private,
  local-only, read-only plugin that runs once a day.
- **Daily runs diff against the previous run**: jobs are marked new,
  unchanged, edited, or gone. A job is marked closed after 2 consecutive
  misses, and reposts are flagged.
- **Funnel**: code-based filters first, then Fit Quotient, then Job Score
  (model-based) on only the top ~20 candidates — to keep model usage cheap.
- **Two scores**:
  - **Fit Quotient**: keyword-overlap percentage between resume and job
    description, computed in code only, no model.
  - **Job Score**: a rubric-based score computed by the model, run only on
    the top ~20 jobs that pass Fit Quotient.
- **Locations**: a ranked list of preferred locations plus an exclude list;
  every job is labeled with a `work_mode` (remote/hybrid/onsite).
- **Dashboard never pads results**: it shows fewer matches rather than
  padding with weak ones.
- **Settings tab** in the dashboard, built for non-technical users.
- **Resume required at setup** — the pipeline doesn't run without one.

## Roadmap

1. *(done — see Current status)*
2. *(done — see Current status)*
3. **Company Finder**
   - 3a. Python project scaffolding with `uv`
   - 3b. ATS detector
   - 3c. Company watchlist
   - 3d. First MCP server
4. **Job Finder**: Greenhouse/Lever/Ashby feeds, a standard job format,
   deduplication, daily comparison (new/unchanged/edited/gone)
5. **Funnel and Job Score**
6. **Dashboard** (web app, run on the user's Mac) with a Settings tab
7. **9am scheduled run**
8. **Fit Quotient and best-resume pick**
9. **More sources and company discovery**
10. **Bulk prepare** (application prep assistance across several jobs)
11. **LinkedIn private plugin**

**Later / someday**: build-a-resume-with-me, warm-intro finder, easy
double-click install, hosted version.

## File structure

Kept up to date as real folders/files are added (not every tiny file —
just the shape of the project).

```
Job Aggregator/
├── PLAN.md              — this file
├── CLAUDE.local.md      — personal preferences (gitignored, not shared)
├── .gitignore
└── job_agent/           — the engine (step 3+), separate from the dashboard
    ├── pyproject.toml   — project metadata + dependencies
    ├── uv.lock          — exact locked dependency versions
    ├── .python-version  — Python version for this project (3.13)
    ├── README.md
    └── src/job_agent/
        └── __init__.py  — placeholder entry point (real code from 3b on)
```

## Current status

- **Step 2 is done**: profile, rubric, setup, and resumes are in place.
- **Step 3a is done**: `job_agent/` scaffolded as a `uv`-managed Python
  project (Python 3.13, `src/job_agent/` package layout).
- **Open items**:
  - Confirm resume summaries.
  - Make must-haves specific (not generic).
- **Next up**: Step 3b — ATS detector.

---

*Keep this file updated as decisions change — it's the source of truth for
what this project is and why, across sessions.*
