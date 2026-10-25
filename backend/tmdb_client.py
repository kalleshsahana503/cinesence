"""
Thin wrapper around the TMDB API: popular/now-playing/upcoming movies, full
details, credits (director/producers/cast), and legal watch-provider links.

Fetches run in parallel (ThreadPoolExecutor) to make ingest much faster —
sequential fetching of 100+ movies (details+credits+providers = 3 calls each)
was the main cause of slow ingestion.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from config import TMDB_API_KEY, TMDB_BASE_URL, WATCH_REGION, TMDB_FETCH_WORKERS

_session = requests.Session()


def _get(path: str, params: dict | None = None) -> dict:
    params = params or {}
    params["api_key"] = TMDB_API_KEY
    resp = _session.get(f"{TMDB_BASE_URL}{path}", params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def fetch_popular_movie_ids(pages: int = 5) -> list[int]:
    ids = []
    for page in range(1, pages + 1):
        data = _get("/movie/popular", {"page": page})
        ids.extend([m["id"] for m in data.get("results", [])])
    return ids


def fetch_now_playing_ids(pages: int = 3) -> list[int]:
    """Movies currently in theaters — keeps the catalog fresh with new releases."""
    ids = []
    for page in range(1, pages + 1):
        data = _get("/movie/now_playing", {"page": page})
        ids.extend([m["id"] for m in data.get("results", [])])
    return ids


def fetch_upcoming_ids(pages: int = 2) -> list[int]:
    """Movies releasing soon — so the catalog isn't only backward-looking."""
    ids = []
    for page in range(1, pages + 1):
        data = _get("/movie/upcoming", {"page": page})
        ids.extend([m["id"] for m in data.get("results", [])])
    return ids


def fetch_ids_by_language(language: str, pages: int = 3) -> list[int]:
    """
    Pull popular movies filtered to a specific original language using TMDB's
    /discover endpoint. Language codes: en=English, hi=Hindi, kn=Kannada,
    mr=Marathi, ta=Tamil, te=Telugu, ml=Malayalam, etc.
    """
    ids = []
    for page in range(1, pages + 1):
        data = _get(
            "/discover/movie",
            {
                "with_original_language": language,
                "sort_by": "popularity.desc",
                "page": page,
            },
        )
        ids.extend([m["id"] for m in data.get("results", [])])
    return ids


def fetch_ids_multilingual(languages: list[str], pages_per_language: int = 3) -> list[int]:
    all_ids = []
    for lang in languages:
        lang_ids = fetch_ids_by_language(lang, pages=pages_per_language)
        print(f"  {lang}: found {len(lang_ids)} movies")
        all_ids.extend(lang_ids)
    return _dedupe(all_ids)


def _dedupe(ids: list[int]) -> list[int]:
    seen = set()
    out = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def fetch_movie_full(movie_id: int) -> dict:
    """Combines details + credits + watch/providers into one row dict."""
    details = _get(f"/movie/{movie_id}")
    credits = _get(f"/movie/{movie_id}/credits")
    providers = _get(f"/movie/{movie_id}/watch/providers")

    director = next(
        (c["name"] for c in credits.get("crew", []) if c.get("job") == "Director"), ""
    )
    producers = ", ".join(
        c["name"] for c in credits.get("crew", []) if c.get("job") == "Producer"
    )
    lead_cast = ", ".join(
        f"{c['name']} as {c.get('character', '?')}"
        for c in sorted(credits.get("cast", []), key=lambda x: x.get("order", 99))[:6]
    )

    region_data = providers.get("results", {}).get(WATCH_REGION, {})
    watch_link = region_data.get("link", "")
    platforms = region_data.get("flatrate", []) or region_data.get("free", [])
    watch_platform = ", ".join(p["provider_name"] for p in platforms) if platforms else ""

    return {
        "id": details["id"],
        "title": details.get("title", ""),
        "overview": details.get("overview", ""),
        "genres": "|".join(g["name"] for g in details.get("genres", [])),
        "poster_path": details.get("poster_path", "") or "",
        "backdrop_path": details.get("backdrop_path", "") or "",
        "vote_average": details.get("vote_average", 0) or 0,
        "release_year": (details.get("release_date") or "")[:4],
        "runtime": details.get("runtime", 0) or 0,
        "director": director,
        "producers": producers,
        "cast": lead_cast,
        "watch_link": watch_link,
        "watch_platform": watch_platform,
        "original_language": details.get("original_language", ""),
    }


def _fetch_full_for_ids(ids: list[int]) -> list[dict]:
    """Fetches details for many movie ids IN PARALLEL — this is the main speed fix."""
    rows = []
    total = len(ids)
    done = 0
    with ThreadPoolExecutor(max_workers=TMDB_FETCH_WORKERS) as pool:
        futures = {pool.submit(fetch_movie_full, mid): mid for mid in ids}
        for future in as_completed(futures):
            mid = futures[future]
            try:
                rows.append(future.result())
            except Exception as e:
                print(f"skip {mid}: {e}")
            done += 1
            if done % 15 == 0 or done == total:
                print(f"fetched {done}/{total}")
    return rows


def fetch_all_popular(pages: int = 5) -> list[dict]:
    ids = fetch_popular_movie_ids(pages)
    return _fetch_full_for_ids(ids)


def fetch_all_multilingual(
    languages: list[str],
    pages_per_language: int = 3,
    include_now_playing: bool = True,
    include_upcoming: bool = True,
) -> list[dict]:
    ids = fetch_ids_multilingual(languages, pages_per_language)
    new_ids = set()

    if include_now_playing:
        now_ids = fetch_now_playing_ids(pages=3)
        print(f"  now playing: found {len(now_ids)} movies")
        new_ids.update(now_ids)
        ids.extend(now_ids)

    if include_upcoming:
        up_ids = fetch_upcoming_ids(pages=2)
        print(f"  upcoming: found {len(up_ids)} movies")
        new_ids.update(up_ids)
        ids.extend(up_ids)

    ids = _dedupe(ids)
    rows = _fetch_full_for_ids(ids)
    for r in rows:
        r["is_new"] = 1 if r["id"] in new_ids else 0
    return rows
