# 🎬 CineSense — Semantic Movie Recommender

Plot/theme-based movie recommendations with real TMDB data (multi-language),
a click-through detail page, legal "where to watch" links, and daily
auto-updates.

**Stack:** FastAPI backend · Chroma vector store · sentence-transformers
embeddings (local, free) · Groq LLM (optional) · SQLite · Streamlit frontend.

## Get your free API keys
- **TMDB**: https://www.themoviedb.org/settings/api → free, instant approval.
- **Groq** (optional): https://console.groq.com/keys

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows PowerShell
pip install -r requirements.txt -c constraints.txt

$env:TMDB_API_KEY="your_key"
$env:GROQ_API_KEY="your_key"    # optional

python ingest.py --pages 3
uvicorn main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

## Why it was slow, and what's fixed

1. **Ingest was fetching movies one at a time.** `tmdb_client.py` now fetches
   movie details in parallel (8 at once by default — change `TMDB_FETCH_WORKERS`
   in `config.py` if you want it faster/slower), which cuts ingest time
   dramatically.
2. **The app was re-fetching everything from the backend on every click**
   (moving the slider, toggling a checkbox). The homepage movie list, recent
   searches, etc. are now cached for 5 minutes (`@st.cache_data(ttl=300)`),
   so the app only hits the backend when data can actually have changed.

## Getting every movie "till now" + regular automatic updates

`ingest.py` now also pulls TMDB's **now playing** and **upcoming** lists
(not just "popular"), so new releases show up, not just older popular titles.
Re-running `ingest.py` is always safe — it updates existing movies rather
than duplicating them.

For **regular automatic updates**, there's a ready-made script —
`backend/auto_update.py` — that handles this for you with no Windows menus,
no signup, and no extra setup:

1. Make sure your `TMDB_API_KEY` (and `GROQ_API_KEY` if you use one) are set
   in that terminal, same as always:
   `$env:TMDB_API_KEY="your_key"`
2. Run: `python auto_update.py`
3. It updates your catalog immediately, then automatically re-runs the
   update every day at 4:00 AM (edit `UPDATE_TIME` near the top of
   `auto_update.py` to change that).
4. Just leave that terminal window open (you can minimize it). As long as
   it's running, your movie catalog keeps itself current — no clicking
   through Task Scheduler menus, no other setup.

If you close that window, updates stop until you run it again — it only
updates while it's actually running, similar to how your backend/frontend
servers work.

## Project structure

```
movie-rag-recommender/
├── backend/
│   ├── main.py             # FastAPI: /recommend, /movie/{id}, /movies, /history, /stats
│   ├── config.py           # settings (TMDB, Groq, DB, Chroma, worker count)
│   ├── tmdb_client.py      # TMDB wrapper — parallel fetch, now-playing/upcoming
│   ├── database.py         # SQLite models: Movie, SearchHistory
│   ├── vectorstore.py      # Chroma + embeddings + semantic_search + Groq explain
│   ├── ingest.py           # run this (or schedule it) to update the catalog
│   ├── daily_update.bat    # for Windows Task Scheduler
│   ├── constraints.txt
│   └── requirements.txt
├── frontend/
│   ├── app.py               # Streamlit: galaxy sidebar, poster rows, detail page
│   └── requirements.txt
└── README.md
```
