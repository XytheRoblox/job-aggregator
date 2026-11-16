from job_agent.ats import detect_from_domain, detect_from_url
from fakes import FakeClient, FakeResponse


def test_detects_greenhouse_from_url():
    match = detect_from_url("https://boards.greenhouse.io/stripe")
    assert match.ats == "greenhouse"
    assert match.slug == "stripe"
    assert match.board_url == "https://boards-api.greenhouse.io/v1/boards/stripe/jobs"
    assert match.source == "url"


def test_detects_lever_from_url():
    match = detect_from_url("https://jobs.lever.co/palantir")
    assert match.ats == "lever"
    assert match.slug == "palantir"
    assert match.board_url == "https://api.lever.co/v0/postings/palantir?mode=json"


def test_detects_ashby_from_url():
    match = detect_from_url("https://jobs.ashbyhq.com/ramp")
    assert match.ats == "ashby"
    assert match.slug == "ramp"
    assert match.board_url == "https://api.ashbyhq.com/posting-api/job-board/ramp"


def test_detects_workday_from_url():
    match = detect_from_url("https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite")
    assert match.ats == "workday"
    assert match.slug == "nvidia/NVIDIAExternalCareerSite"
    assert match.board_url == (
        "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs"
    )


def test_unknown_url_returns_none():
    assert detect_from_url("https://example.com/careers") is None


def test_url_with_no_path_returns_none():
    assert detect_from_url("https://boards.greenhouse.io") is None


def test_domain_guessing_probes_until_a_match():
    greenhouse_url = "https://boards-api.greenhouse.io/v1/boards/figma/jobs"
    client = FakeClient(get_responses={greenhouse_url: FakeResponse({"jobs": []}, status_code=200)})

    match = detect_from_domain("figma.com", client=client)

    assert match.ats == "greenhouse"
    assert match.slug == "figma"
    assert match.source == "probed"


def test_domain_guessing_returns_none_when_nothing_matches():
    client = FakeClient(get_responses={})  # every probe falls through to the 404 default
    assert detect_from_domain("not-a-real-company-xyz.com", client=client) is None
