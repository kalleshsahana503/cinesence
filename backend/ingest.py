"""
Pulls movies live from TMDB across multiple languages (English, Hindi,
Kannada, Marathi by default) PLUS current now-playing and upcoming releases,
so the catalog stays current. Fetches run in parallel for speed.

Saves structured data into SQLite and embeds title+genres+plot into Chroma.

Usage:
    python ingest.py
    python ingest.py --pages 3
    python ingest.py --languages en,hi,kn,mr,ta,te
    python ingest.py --no-new          # skip now-playing/upcoming, languages only

This same command is what a daily scheduled task should run — see README.md
for how to set up automatic daily updates with Windows Task Scheduler (free,
built into Windows, no extra software needed).

Requires TMDB_API_KEY to be set (see README).
"""
import argparse
import time

from config import TMDB_API_KEY
from tmdb_client import fetch_all_multilingual
from database import init_db, upsert_movie, get_movie_count
from vectorstore import upsert_movies_into_vectorstore

DEFAULT_LANGUAGES = ["en", "hi", "kn", "mr"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=3, help="Pages per language (20 movies/page)")
    parser.add_argument(
        "--languages",
        type=str,
        default=",".join(DEFAULT_LANGUAGES),
        help="Comma-separated TMDB language codes, e.g. en,hi,kn,mr,ta,te,ml",
    )
    parser.add_argument(
        "--no-new", action="store_true",
        help="Skip now-playing/upcoming fetch (language rows only)",
    )
    args = parser.parse_args()
    languages = [l.strip() for l in args.languages.split(",") if l.strip()]

    if not TMDB_API_KEY:
        raise SystemExit(
            "TMDB_API_KEY is not set. Get a free key at "
            "https://www.themoviedb.org/settings/api and export it as TMDB_API_KEY."
        )

    start = time.time()
    init_db()

    print(f"Fetching movies for languages: {languages} ({args.pages} pages each)...")
    rows = fetch_all_multilingual(
        languages,
        pages_per_language=args.pages,
        include_now_playing=not args.no_new,
        include_upcoming=not args.no_new,
    )
    print(f"Fetched {len(rows)} unique movies.")

    print("Saving structured data to SQLite...")
    for r in rows:
        upsert_movie(r)

    print("Embedding into Chroma for semantic search...")
    upsert_movies_into_vectorstore(rows)

    elapsed = time.time() - start
    total = get_movie_count()
    print(f"Done in {elapsed:.1f}s. Ingested/updated {len(rows)} movies this run. {total} total movies in database.")


if __name__ == "__main__":
    main()
