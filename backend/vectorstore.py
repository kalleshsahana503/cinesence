"""
Chroma vector store + LangChain retrieval for semantic (plot/theme-based)
movie recommendations, with an optional Groq LLM step to explain the match.
"""
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, GROQ_API_KEY, GROQ_MODEL

_embeddings = None
_vectorstore = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=get_embeddings(),
            persist_directory=CHROMA_DIR,
        )
    return _vectorstore


def build_documents_from_rows(rows: list[dict]) -> list[Document]:
    """rows: dicts with id, title, genres, overview, poster_path, release_year."""
    docs = []
    for r in rows:
        text = f"Title: {r['title']}\nGenres: {r.get('genres', '')}\nPlot: {r.get('overview', '')}"
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "id": str(r.get("id", "")),
                    "title": r["title"],
                    "genres": r.get("genres", ""),
                    "overview": r.get("overview", ""),
                    "poster_path": r.get("poster_path", "") or "",
                    "year": r.get("release_year", r.get("year", "")),
                },
            )
        )
    return docs


def upsert_movies_into_vectorstore(rows: list[dict]):
    """Adds/updates movies in Chroma. Safe to call repeatedly (e.g. daily) —
    re-adding the same id overwrites its embedding rather than duplicating it."""
    docs = build_documents_from_rows(rows)
    vs = get_vectorstore()
    ids = [d.metadata["id"] for d in docs]
    vs.add_documents(docs, ids=ids)


def semantic_search(query: str, k: int = 8):
    """Pure vector similarity search — this IS the recommendation engine."""
    vs = get_vectorstore()
    results = vs.similarity_search_with_score(query, k=k)
    out = []
    for doc, score in results:
        item = dict(doc.metadata)
        # Chroma returns a distance (lower = more similar); convert to a
        # 0-1 "similarity" score that's intuitive to display in the UI.
        item["similarity"] = round(max(0.0, 1.0 - float(score)), 3)
        out.append(item)
    return out


_groq_llm = None


def explain_recommendation(query: str, movie: dict) -> str:
    """
    Optional generative step (the 'G' in RAG): ask Groq to explain in one
    sentence why this movie fits the query. Skipped gracefully if no
    GROQ_API_KEY is set — semantic search still works without it.
    """
    global _groq_llm
    if not GROQ_API_KEY:
        return ""
    try:
        if _groq_llm is None:
            from langchain_groq import ChatGroq

            _groq_llm = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0.4)

        prompt = (
            f"User is looking for a movie matching: \"{query}\".\n"
            f"Candidate movie: {movie['title']} — {movie.get('overview', '')}\n"
            "In one short sentence, explain why this movie fits what the user wants."
        )
        resp = _groq_llm.invoke(prompt)
        return resp.content.strip()
    except Exception as e:
        print(f"Groq explain failed: {e}")
        return ""
