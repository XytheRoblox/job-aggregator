"""Track the companies we're watching for job postings.

Each company is tagged with its ATS (Greenhouse/Lever/Ashby) using the
detector in ats.py, so step 4 (Job Finder) knows how to pull its jobs.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from job_agent.ats import ATSMatch, detect_ats

DEFAULT_WATCHLIST_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "watchlist.json"


@dataclass
class Company:
    name: str
    careers_url: str
    ats: str | None = None
    slug: str | None = None
    board_url: str | None = None

    @classmethod
    def from_match(cls, name: str, careers_url: str, match: ATSMatch | None) -> Company:
        if match is None:
            return cls(name=name, careers_url=careers_url)
        return cls(
            name=name,
            careers_url=careers_url,
            ats=match.ats,
            slug=match.slug,
            board_url=match.board_url,
        )


def load_watchlist(path: Path = DEFAULT_WATCHLIST_PATH) -> list[Company]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    return [Company(**item) for item in raw]


def save_watchlist(companies: list[Company], path: Path = DEFAULT_WATCHLIST_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(c) for c in companies], indent=2))


def add_company(name: str, careers_url: str, path: Path = DEFAULT_WATCHLIST_PATH) -> Company:
    """Detect a company's ATS and add it to the watchlist (updating it if already present)."""
    companies = [c for c in load_watchlist(path) if c.name != name]
    company = Company.from_match(name, careers_url, detect_ats(careers_url))
    companies.append(company)
    save_watchlist(companies, path)
    return company
