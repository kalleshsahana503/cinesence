"""
DuckDuckGo lookup — free, no API key required, unlike most search APIs.

Used to give a quick extra snippet about a movie plus a live search link,
supplementing (not replacing) TMDB's structured data.
"""
import requests

_session = requests.Session()


def duckduckgo_summary(query: str) -> dict:
    """
    Uses DuckDuckGo's free Instant Answer API (no key needed) to fetch a
    short summary if one exists. Returns an empty summary gracefully if
    DuckDuckGo has nothing indexed for this exact query - that's normal for
    many movies, not an error.
    """
    try:
        resp = _session.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        summary = data.get("AbstractText") or ""
        source = data.get("AbstractSource") or ""
    except Exception:
        summary = ""
        source = ""

    return {
        "summary": summary,
        "source": source,
        "search_url": f"https://duckduckgo.com/?q={requests.utils.quote(query)}",
    }
