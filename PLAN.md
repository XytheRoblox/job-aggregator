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

## Current status

- **Step 2 is done**: profile, rubric, setup, and resumes are in place.
- **Open items**:
  - Confirm resume summaries.
  - Make must-haves specific (not generic).
- **Next up**: Step 3a — Python project scaffolding with `uv`.

---

*Keep this file updated as decisions change — it's the source of truth for
what this project is and why, across sessions.*
