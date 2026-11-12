"""Detect which Applicant Tracking System (ATS) a company uses.

Supports Greenhouse, Lever, and Ashby. Detection works two ways:
1. From a known careers page URL (pattern match, no network call).
2. From just a company name or domain (guess a slug, then probe each
   ATS's public API to see which one responds).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

GREENHOUSE_HOSTS = {"boards.greenhouse.io", "job-boards.greenhouse.io"}
LEVER_HOSTS = {"jobs.lever.co"}
ASHBY_HOSTS = {"jobs.ashbyhq.com"}

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
LEVER_API = "https://api.lever.co/v0/postings/{slug}?mode=json"
ASHBY_API = "https://api.ashbyhq.com/posting-api/job-board/{slug}"


@dataclass
class ATSMatch:
    ats: str  # "greenhouse", "lever", or "ashby"
    slug: str  # the company's identifier on that ATS
    board_url: str  # the API URL to fetch jobs from
    source: str  # "url" (matched a known careers URL) or "probed" (guessed + confirmed)


def detect_from_url(url: str) -> ATSMatch | None:
    """Match a careers page URL against known ATS hosting patterns."""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = parsed.netloc.lower()
    slug = parsed.path.strip("/").split("/")[0]
    if not slug:
        return None

    if host in GREENHOUSE_HOSTS:
        return ATSMatch("greenhouse", slug, GREENHOUSE_API.format(slug=slug), "url")
    if host in LEVER_HOSTS:
        return ATSMatch("lever", slug, LEVER_API.format(slug=slug), "url")
    if host in ASHBY_HOSTS:
        return ATSMatch("ashby", slug, ASHBY_API.format(slug=slug), "url")
    return None


def _slug_candidates(name_or_domain: str) -> list[str]:
    """Guess possible ATS slugs from a company name or domain."""
    text = re.sub(r"^https?://", "", name_or_domain.lower().strip())
    text = text.split("/")[0].removeprefix("www.")
    domain_label = text.split(".")[0]

    candidates = [domain_label]
    plain_name = re.sub(r"[^a-z0-9]", "", name_or_domain.lower())
    if plain_name and plain_name not in candidates:
        candidates.append(plain_name)
    return candidates


def _probe(client: httpx.Client, api_url: str) -> bool:
    try:
        response = client.get(api_url, timeout=5.0)
    except httpx.HTTPError:
        return False
    return response.status_code == 200


def detect_from_domain(name_or_domain: str, client: httpx.Client | None = None) -> ATSMatch | None:
    """Guess a company's ATS slug and confirm it by probing each API."""
    owns_client = client is None
    client = client or httpx.Client()
    try:
        for slug in _slug_candidates(name_or_domain):
            for ats, api_template in (
                ("greenhouse", GREENHOUSE_API),
                ("lever", LEVER_API),
                ("ashby", ASHBY_API),
            ):
                api_url = api_template.format(slug=slug)
                if _probe(client, api_url):
                    return ATSMatch(ats, slug, api_url, "probed")
        return None
    finally:
        if owns_client:
            client.close()


def detect_ats(company: str) -> ATSMatch | None:
    """Detect a company's ATS from a careers URL, domain, or name."""
    return detect_from_url(company) or detect_from_domain(company)
