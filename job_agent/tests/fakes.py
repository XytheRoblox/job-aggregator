"""A minimal stand-in for httpx.Client, so tests don't hit the real network.

Response shapes used across tests are copied from real API calls made
during development (Stripe/Greenhouse, Palantir/Lever, Ramp/Ashby,
NVIDIA/Workday), not invented, so a test failing here means something
really did change.
"""

from __future__ import annotations


class FakeResponse:
    def __init__(self, json_data=None, status_code=200, text=""):
        self._json = json_data
        self.status_code = status_code
        self.text = text or str(json_data)

    def json(self):
        return self._json


class FakeClient:
    """get_responses maps URL -> FakeResponse. post_handler(url, json) -> FakeResponse."""

    def __init__(self, get_responses=None, post_handler=None):
        self.get_responses = get_responses or {}
        self.post_handler = post_handler
        self.get_calls: list[str] = []
        self.post_calls: list[tuple[str, dict]] = []

    def get(self, url, timeout=None):
        self.get_calls.append(url)
        if url not in self.get_responses:
            return FakeResponse(status_code=404, text="not found")
        return self.get_responses[url]

    def post(self, url, json=None, timeout=None):
        self.post_calls.append((url, json))
        return self.post_handler(url, json)
