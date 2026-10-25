import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ---- Vector store ----
CHROMA_DIR = str(BASE_DIR / "chroma_db")
COLLECTION_NAME = "movies"

# Local embedding model (no API key needed, runs on your machine).
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ---- Groq (LLM step: "why this movie fits your search") ----
# Free key: https://console.groq.com/keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"

# ---- TMDB (movie data, cast/crew, posters, watch providers) ----
# Free key: https://www.themoviedb.org/settings/api (the v3 "API Key")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# Country used to pick watch-provider links (change to your region's code, e.g. "IN")
WATCH_REGION = os.environ.get("WATCH_REGION", "US")

# How many pages per language to ingest (20 movies per page)
TMDB_PAGES_PER_LANGUAGE = int(os.environ.get("TMDB_PAGES_PER_LANGUAGE", "3"))

# How many parallel workers to use when fetching movie details from TMDB.
# Higher = faster ingest, but don't push too high or TMDB may rate-limit you.
TMDB_FETCH_WORKERS = int(os.environ.get("TMDB_FETCH_WORKERS", "8"))

# ---- OMDb (free, unpaid alternative source — used here for IMDb ratings) ----
# Free key: https://www.omdbapi.com/apikey.aspx (1,000 free requests/day)
OMDB_API_KEY = os.environ.get("OMDB_API_KEY", "")
OMDB_BASE_URL = "https://www.omdbapi.com/"

# ---- Database (movies + search history) ----
DATABASE_URL = f"sqlite:///{BASE_DIR / 'app.db'}"
