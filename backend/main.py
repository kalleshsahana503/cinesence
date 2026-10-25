import re
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import (
    init_db,
    log_search,
    get_recent_searches,
    get_movie,
    get_all_movies,
    get_all_genres,
    get_all_languages,
    get_movie_count,
)
from vectorstore import semantic_search, explain_recommendation, get_vectorstore
from web_lookup import duckduckgo_summary
from omdb_client import get_imdb_info
from config import TMDB_IMAGE_BASE

TMDB_BACKDROP_BASE = "https://image.tmdb.org/t/p/w1280"

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "kn": "Kannada", "mr": "Marathi",
    "ta": "Tamil", "te": "Telugu", "ml": "Malayalam", "bn": "Bengali",
    "pa": "Punjabi", "gu": "Gujarati",
}

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "on", "at", "to", "for", "with",
    "is", "are", "was", "were", "who", "that", "this", "his", "her", "their",
    "story", "about", "movie", "film",
}

app = FastAPI(title="CineSense Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


@app.on_event("startup")
def warm_up():
    """Preloads the embedding model + vector store at server start, so the
    FIRST search a user makes isn't slow — that startup cost happens once
    here instead of during someone's first click."""
    try:
        get_vectorstore()
        print("Vector store warmed up and ready.")
    except Exception as e:
        print(f"Warm-up skipped: {e}")


# ---- Simple in-memory TTL cache for read-heavy endpoints ----
_cache: dict = {}
CACHE_TTL_SECONDS = 60


def cached(key, fn, ttl=CACHE_TTL_SECONDS):
    now = time.time()
    entry = _cache.get(key)
    if entry and now - entry[0] < ttl:
        return entry[1]
    value = fn()
    _cache[key] = (now, value)
    return value


def _serialize_movie(m):
    return {
        "id": m.id,
        "title": m.title,
        "overview": m.overview,
        "genres": m.genres,
        "poster_url": f"{TMDB_IMAGE_BASE}{m.poster_path}" if m.poster_path else None,
        "backdrop_url": f"{TMDB_BACKDROP_BASE}{m.backdrop_path}" if m.backdrop_path else None,
        "vote_average": m.vote_average,
        "release_year": m.release_year,
        "runtime": m.runtime,
        "director": m.director,
        "producers": m.producers,
        "cast": m.cast,
        "watch_link": m.watch_link,
        "watch_platform": m.watch_platform,
        "original_language": m.original_language,
        "is_new": bool(m.is_new),
    }


def _default_why(query: str, movie: dict) -> str:
    """
    Always-available 'why this matches' explanation — no LLM needed.
    Finds words shared between the search query and the movie's own
    plot/genres, so every result gets a short, honest reason.
    """
    def words(text):
        return {w for w in re.findall(r"[a-zA-Z']+", (text or "").lower()) if w not in STOPWORDS and len(w) > 2}

    query_words = words(query)
    movie_words = words(movie.get("overview", "")) | words((movie.get("genres", "") or "").replace("|", " "))
    shared = sorted(query_words & movie_words)[:4]
    if shared:
        return f"Matches on: {', '.join(shared)}"
    return "Close semantic match on plot and theme"


class RecommendRequest(BaseModel):
    query: str
    k: int = 8
    explain: bool = False


@app.post("/recommend")
def recommend(req: RecommendRequest):
    results = semantic_search(req.query, k=req.k)
    for r in results:
        r["poster_url"] = (
            f"{TMDB_IMAGE_BASE}{r['poster_path']}" if r.get("poster_path") else None
        )
        if req.explain:
            r["why"] = explain_recommendation(req.query, r) or _default_why(req.query, r)
        else:
            r["why"] = _default_why(req.query, r)
    log_search(req.query, [r["title"] for r in results])
    return {"query": req.query, "results": results}


@app.get("/movie/{movie_id}")
def movie_detail(movie_id: int):
    m = get_movie(movie_id)
    if not m:
        raise HTTPException(status_code=404, detail="Movie not found. Run ingest.py first.")
    return _serialize_movie(m)


@app.get("/movie/{movie_id}/similar")
def similar_movies(movie_id: int, k: int = 8):
    m = get_movie(movie_id)
    if not m:
        raise HTTPException(status_code=404, detail="Movie not found.")
    query = f"{m.title}. {m.overview}"
    results = semantic_search(query, k=k + 1)
    results = [r for r in results if r["id"] != str(movie_id)][:k]
    for r in results:
        r["poster_url"] = (
            f"{TMDB_IMAGE_BASE}{r['poster_path']}" if r.get("poster_path") else None
        )
    return {"results": results}


@app.get("/movies")
def list_movies(limit: int = 400, genre: str | None = None, language: str | None = None, new_only: bool = False):
    key = ("movies", limit, genre, language, new_only)
    rows = cached(key, lambda: get_all_movies(limit=limit, genre=genre, language=language, new_only=new_only))
    return {"results": [_serialize_movie(m) for m in rows]}


@app.get("/genres")
def list_genres():
    genres = cached("genres", get_all_genres, ttl=300)
    return {"genres": genres}


@app.get("/languages")
def list_languages():
    codes = cached("languages", get_all_languages, ttl=300)
    return {"languages": [{"code": c, "name": LANGUAGE_NAMES.get(c, c.upper())} for c in codes]}


@app.get("/movie/{movie_id}/web")
def movie_web_info(movie_id: int):
    """Free, no-key lookup — a quick extra summary plus a live search link."""
    m = get_movie(movie_id)
    if not m:
        raise HTTPException(status_code=404, detail="Movie not found.")
    info = duckduckgo_summary(f"{m.title} {m.release_year} movie")
    return info


@app.get("/movie/{movie_id}/rating")
def movie_rating_info(movie_id: int):
    """A second, different free data source (OMDb) — supplies the IMDb rating."""
    m = get_movie(movie_id)
    if not m:
        raise HTTPException(status_code=404, detail="Movie not found.")
    return get_imdb_info(m.title, m.release_year)


@app.get("/history")
def history(limit: int = 20):
    rows = get_recent_searches(limit)
    return [
        {"query": r.query, "top_titles": r.top_result_titles, "created_at": r.created_at}
        for r in rows
    ]


@app.get("/stats")
def stats():
    return {"movie_count": get_movie_count()}


@app.get("/health")
def health():
    return {"status": "ok"}
