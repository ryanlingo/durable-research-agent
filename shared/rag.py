"""Simple RAG over a fixed local corpus.

Uses OpenAI embeddings + cosine similarity. Designed to be identical
in both the Temporal and non-Temporal implementations.
"""

from __future__ import annotations

import math
from pathlib import Path

from openai import OpenAI

from .config import EMBEDDING_MODEL
from .types import RetrievedChunk, TokenUsage

DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "docs"


def _load_documents() -> list[dict]:
    docs = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        # Split into rough chunks by paragraph
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for i, para in enumerate(paragraphs):
            docs.append(
                {
                    "doc_id": f"{path.stem}_{i}",
                    "title": path.stem.replace("_", " ").title(),
                    "content": para,
                }
            )
    return docs


_CORPUS = _load_documents()
_EMBEDDINGS: list[list[float]] | None = None


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _get_embeddings(texts: list[str]) -> tuple[list[list[float]], TokenUsage]:
    client = OpenAI()
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    usage = TokenUsage(
        prompt_tokens=resp.usage.prompt_tokens if resp.usage else 0,
        total_tokens=resp.usage.total_tokens if resp.usage else 0,
    )
    vectors = [item.embedding for item in resp.data]
    return vectors, usage


def ensure_index() -> TokenUsage:
    """Embed the corpus once (lazy). Returns token usage of the embedding call."""
    global _EMBEDDINGS
    if _EMBEDDINGS is not None:
        return TokenUsage()
    texts = [d["content"] for d in _CORPUS]
    if not texts:
        _EMBEDDINGS = []
        return TokenUsage()
    vectors, usage = _get_embeddings(texts)
    _EMBEDDINGS = vectors
    return usage


def retrieve(query: str, k: int = 4) -> tuple[list[RetrievedChunk], TokenUsage]:
    """Return top-k chunks for the query plus embedding token usage."""
    usage = ensure_index()
    if not _CORPUS or _EMBEDDINGS is None:
        return [], usage

    q_vectors, q_usage = _get_embeddings([query])
    usage.add(q_usage)
    q_vec = q_vectors[0]

    scored = []
    for doc, emb in zip(_CORPUS, _EMBEDDINGS, strict=False):
        score = _cosine(q_vec, emb)
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)

    chunks = [
        RetrievedChunk(
            doc_id=doc["doc_id"],
            title=doc["title"],
            content=doc["content"],
            score=score,
        )
        for score, doc in scored[:k]
    ]
    return chunks, usage
