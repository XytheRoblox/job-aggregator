"""The job_agent MCP server.

Exposes the engine's capabilities as tools an MCP-aware client (like
Claude) can call directly, instead of you running Python by hand.
For now that's just watchlist management; more tools get added as
later roadmap steps (Job Finder, Job Score, ...) land.
"""

from __future__ import annotations

from dataclasses import asdict

from mcp.server.mcpserver import MCPServer

from job_agent.watchlist import Company, add_company, load_watchlist

mcp = MCPServer("job-agent")


@mcp.tool()
def watchlist_add(name: str, careers_url: str) -> dict:
    """Add a company to the watchlist, detecting its ATS (Greenhouse/Lever/Ashby)."""
    company: Company = add_company(name, careers_url)
    return asdict(company)


@mcp.tool()
def watchlist_list() -> list[dict]:
    """List every company currently on the watchlist."""
    return [asdict(c) for c in load_watchlist()]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
