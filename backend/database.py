"""
Database layer — SQLite via SQLAlchemy.

Two tables:
  - Movie: full structured record per movie (separate columns)
  - SearchHistory: log of every search query made

To move to Postgres later: change DATABASE_URL in config.py to a
postgresql:// URL and `pip install psycopg2-binary` — nothing else changes.
"""
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)  # TMDB movie id
    title = Column(String, nullable=False, index=True)
    overview = Column(Text)
    genres = Column(String)          # "Action|Sci-Fi"
    poster_path = Column(String)
    backdrop_path = Column(String)
    vote_average = Column(String)
    release_year = Column(String)
    runtime = Column(Integer)
    director = Column(String)
    producers = Column(String)       # comma-separated
    cast = Column(Text)              # "Name as Character, Name as Character, ..."
    watch_link = Column(String)      # legal deep link (TMDB watch-providers / JustWatch)
    watch_platform = Column(String)  # e.g. "Netflix, Prime Video"
    original_language = Column(String)  # e.g. "en", "hi", "kn", "mr"
    is_new = Column(Integer, default=0)  # 1 if sourced from now-playing/upcoming
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    top_result_titles = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def upsert_movie(row: dict):
    db = SessionLocal()
    try:
        row = dict(row)
        row.pop("last_updated", None)
        existing = db.query(Movie).filter(Movie.id == row["id"]).first()
        if existing:
            for k, v in row.items():
                setattr(existing, k, v)
            existing.last_updated = datetime.utcnow()
        else:
            db.add(Movie(**row, last_updated=datetime.utcnow()))
        db.commit()
    finally:
        db.close()


def get_movie(movie_id: int) -> Movie | None:
    db = SessionLocal()
    try:
        return db.query(Movie).filter(Movie.id == movie_id).first()
    finally:
        db.close()


def get_all_movies(limit: int = 100, genre: str | None = None, language: str | None = None, new_only: bool = False):
    db = SessionLocal()
    try:
        q = db.query(Movie)
        if genre:
            q = q.filter(Movie.genres.contains(genre))
        if language:
            q = q.filter(Movie.original_language == language)
        if new_only:
            q = q.filter(Movie.is_new == 1)
        return q.order_by(Movie.vote_average.desc()).limit(limit).all()
    finally:
        db.close()


def get_all_genres() -> list[str]:
    db = SessionLocal()
    try:
        rows = db.query(Movie.genres).all()
        genre_set = set()
        for (g,) in rows:
            if g:
                genre_set.update(g.split("|"))
        return sorted(genre_set)
    finally:
        db.close()


def get_all_languages() -> list[str]:
    db = SessionLocal()
    try:
        rows = db.query(Movie.original_language).distinct().all()
        return sorted({r[0] for r in rows if r[0]})
    finally:
        db.close()


def log_search(query: str, top_titles: list[str]):
    db = SessionLocal()
    try:
        db.add(SearchHistory(query=query, top_result_titles=", ".join(top_titles)))
        db.commit()
    finally:
        db.close()


def get_recent_searches(limit: int = 20):
    db = SessionLocal()
    try:
        return (
            db.query(SearchHistory)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()


def get_movie_count() -> int:
    db = SessionLocal()
    try:
        return db.query(Movie).count()
    finally:
        db.close()
