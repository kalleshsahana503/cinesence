"""
OMDb — a second, different, free/unpaid movie data source (not TMDB).
Used here to pull the IMDb rating as a supplementary data point.

Free key (1,000 requests/day, no cost ever): https://www.omdbapi.com/apikey.aspx
Gracefully returns nothing if no key is set — this is optional, not required.
"""
import requests

from config import OMDB_API_KEY, OMDB_BASE_URL

_session = requests.Session()


def get_imdb_info(title: str, year: str = "") -> dict:
    if not OMDB_API_KEY:
        return {}
    try:
        params = {"apikey": OMDB_API_KEY, "t": title}
        if year:
            params["y"] = year
        resp = _session.get(OMDB_BASE_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if data.get("Response") != "True":
            return {}
        return {
            "imdb_rating": data.get("imdbRating", ""),
            "imdb_votes": data.get("imdbVotes", ""),
            "imdb_id": data.get("imdbID", ""),
            "imdb_url": f"https://www.imdb.com/title/{data.get('imdbID', '')}/" if data.get("imdbID") else "",
        }
    except Exception:
        return {}
