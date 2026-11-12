"""Detect which Applicant Tracking System (ATS) a company uses.

Supports Greenhouse, Lever, Ashby, and Workday. Detection works two ways:
1. From a known careers page URL (pattern match, no network call).
2. From just a company name or domain (guess a slug, then probe each
   ATS's public API to see which one responds) — Greenhouse/Lever/Ashby
   only. Workday can't be guessed this way: its careers URL needs both a
   tenant *and* an arbitrary site name chosen by the company (e.g.
   "nvidia" + "NVIDIAExternalCareerSite"), so it's only detected when we
   already have the full URL.

Workday's job API is unofficial — Workday doesn't publish or version it,
it's just the same internal endpoint the careers webpage calls. It can
also change shape without notice, and (unlike the other three, which use
GET) it's called with POST and a JSON body. Step 4's fetcher needs to
treat a broken/changed Workday response as a loud failure, not silently
skip it the way a failed probe is treated above for the other three.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

GREENHOUSE_HOSTS = {"boards.greenhouse.io", "job-boards.greenhouse.io"}
LEVER_HOSTS = {"jobs.lever.co"}
ASHBY_HOSTS = {"jobs.ashbyhq.com"}
WORKDAY_HOST_PATTERN = re.compile(r"^(?P<tenant>[^.]+)\.(?P<datacenter>wd\d+)\.myworkdayjobs\.com$")

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
LEVER_API = "https://api.lever.co/v0/postings/{slug}?mode=json"
ASHBY_API = "https://api.ashbyhq.com/posting-api/job-board/{slug}"
WORKDAY_API = "https://{tenant}.{datacenter}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"


@dataclass
class ATSMatch:
    ats: str  # "greenhouse", "lever", "ashby", or "workday"
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

    workday_host = WORKDAY_HOST_PATTERN.match(host)
    if workday_host:
        tenant = workday_host["tenant"]
        datacenter = workday_host["datacenter"]
        board_url = WORKDAY_API.format(tenant=tenant, datacenter=datacenter, site=slug)
        return ATSMatch("workday", f"{tenant}/{slug}", board_url, "url")
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
