import job_agent.watchlist as watchlist_module
from job_agent.watchlist import Company, add_company, load_watchlist, save_watchlist


def test_add_company_detects_ats_and_persists(tmp_path):
    path = tmp_path / "watchlist.json"

    # "https://boards.greenhouse.io/stripe" matches a known ATS host directly,
    # so detect_ats resolves it from the URL pattern alone — no network call.
    company = add_company("Stripe", "https://boards.greenhouse.io/stripe", path=path)

    assert company.ats == "greenhouse"
    assert company.slug == "stripe"
    assert load_watchlist(path) == [company]


def test_add_company_with_unknown_ats_still_gets_added(tmp_path, monkeypatch):
    # an unrecognized URL would otherwise fall through to detect_from_domain,
    # which makes real network calls — not something a unit test should do.
    monkeypatch.setattr(watchlist_module, "detect_ats", lambda careers_url: None)
    path = tmp_path / "watchlist.json"

    company = add_company("Mystery Co", "https://example.com/careers", path=path)

    assert company.ats is None
    assert load_watchlist(path) == [company]


def test_add_company_updates_existing_entry_by_name(tmp_path):
    path = tmp_path / "watchlist.json"
    add_company("Stripe", "https://boards.greenhouse.io/stripe", path=path)

    add_company("Stripe", "https://jobs.lever.co/stripe", path=path)

    companies = load_watchlist(path)
    assert len(companies) == 1
    assert companies[0].ats == "lever"


def test_load_watchlist_returns_empty_list_when_no_file(tmp_path):
    assert load_watchlist(tmp_path / "does-not-exist.json") == []


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "watchlist.json"
    companies = [
        Company(name="A", careers_url="https://a.com", ats="greenhouse", slug="a", board_url="https://x/a"),
        Company(name="B", careers_url="https://b.com", ats=None, slug=None, board_url=None),
    ]

    save_watchlist(companies, path)

    assert load_watchlist(path) == companies
