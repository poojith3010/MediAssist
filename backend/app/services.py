from dataclasses import dataclass
import json
from typing import Iterable

import httpx

from .config import get_settings
from .models import Document, DocumentChunk


@dataclass
class RetrievedChunk:
    document: Document
    content: str
    page_number: int | None


def _lexical_retrieve(question: str, documents: list[Document], limit: int) -> list[RetrievedChunk]:
    terms = {term.lower() for term in question.split() if len(term) > 2}
    scored: list[tuple[int, RetrievedChunk]] = []
    for document in documents:
        for chunk in document.chunks:
            score = sum(term in chunk.content.lower() for term in terms)
            if score:
                scored.append((score, RetrievedChunk(document, chunk.content, chunk.page_number)))
    return [item for _, item in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]


def _embed(texts: list[str]) -> list[list[float]]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(get_settings().embedding_model)
    return model.encode(texts, normalize_embeddings=True).tolist()


def index_chunks(chunks: Iterable[DocumentChunk]) -> None:
    chunk_list = list(chunks)
    if not chunk_list:
        return
    try:
        vectors = _embed([chunk.content for chunk in chunk_list])
    except ImportError:
        return
    for chunk, vector in zip(chunk_list, vectors):
        chunk.embedding = json.dumps(vector)


def retrieve(question: str, documents: list[Document], limit: int = 4) -> list[RetrievedChunk]:
    chunks = [chunk for document in documents for chunk in document.chunks if chunk.embedding]
    if not chunks:
        return _lexical_retrieve(question, documents, limit)
    try:
        import numpy as np
        import faiss

        vectors = np.asarray([json.loads(chunk.embedding) for chunk in chunks], dtype="float32")
        query = np.asarray(_embed([question]), dtype="float32")
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        _, positions = index.search(query, min(limit, len(chunks)))
        by_id = {chunk.id: chunk for chunk in chunks}
        selected = [by_id[chunks[position].id] for position in positions[0] if position >= 0]
        return [RetrievedChunk(next(doc for doc in documents if doc.id == chunk.document_id), chunk.content, chunk.page_number) for chunk in selected]
    except ImportError:
        return _lexical_retrieve(question, documents, limit)


async def ask_ollama(question: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "The available documents do not establish an answer to that question."
    context = "\n\n".join(f"[{c.document.filename}, page {c.page_number or '?'}] {c.content}" for c in chunks)
    prompt = (
        "You are an educational healthcare information assistant. Use only the supplied context. "
        "If it does not support an answer, say so. Do not diagnose or prescribe.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )
    settings = get_settings()
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        payload = response.json()
    answer = payload.get("response")
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("Local model returned an invalid response")
    return answer.strip()


async def summarize_with_ollama(document: Document) -> str:
    if not document.extracted_text.strip():
        return "No text was extracted from this document. OCR is required before summarization."
    prompt = (
        "Summarize the following healthcare document for educational use. "
        "Use only the text, preserve uncertainty, do not diagnose or prescribe, and mention when extraction may be incomplete.\n\n"
        f"Document:\n{document.extracted_text[:30000]}"
    )
    settings = get_settings()
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        answer = response.json().get("response")
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("Local model returned an invalid summary")
    return answer.strip()
