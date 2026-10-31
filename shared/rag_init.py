"""
Lightman knowledge base (RAG) backend.

Embeddings are computed locally by ChromaDB's DefaultEmbeddingFunction
(ONNXMiniLM_L6_V2, 384-dim). No external API and no API key are required —
the model is downloaded once on first use and cached on disk
(usually under ~/.cache/chroma/onnx_models/).

Public API:
    train_knowledge_base(text_content, source_name) -> int
    search_knowledge_base(query, n_results=3) -> list[str]

Convenience helpers:
    train_from_file(path, source_name=None) -> int
    knowledge_base_size() -> int
    clear_knowledge_base() -> None
"""

import hashlib
import logging
import os
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CACHE_DIR = ".lightman_cache/rag"
COLLECTION_NAME = "knowledge"
CHUNK_SIZE = 500


# ---------------------------------------------------------------------------
# ChromaDB plumbing
# ---------------------------------------------------------------------------

def _get_client() -> chromadb.PersistentClient:
    """Return a persistent ChromaDB client rooted at CACHE_DIR."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    return chromadb.PersistentClient(
        path=CACHE_DIR,
        settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
    )


def _get_collection(client: Optional[chromadb.PersistentClient] = None):
    """
    Return (or create) the shared 'knowledge' collection.

    Bound to ChromaDB's local DefaultEmbeddingFunction, so every upsert
    and every query is embedded on the machine — nothing leaves the
    process and no API key is involved.
    """
    if client is None:
        client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=DefaultEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def _chunk_text(text_content: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """
    Split `text_content` into roughly `chunk_size`-character chunks.

    Prefers natural boundaries (paragraph -> sentence -> word) but
    always falls back to a hard cut so long unbroken strings are
    still chunked. Empty / whitespace-only chunks are discarded.
    """
    text = (text_content or "").strip()
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)

        if end < n:
            snap = text.rfind("\n", start, end)
            if snap == -1 or snap < start + chunk_size // 2:
                snap = text.rfind(". ", start, end)
            if snap == -1 or snap < start + chunk_size // 2:
                snap = text.rfind(" ", start, end)
            if snap != -1 and snap > start:
                end = snap + (1 if text[snap] == "." else 0)

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end

    return chunks


# ---------------------------------------------------------------------------
# Stable IDs
# ---------------------------------------------------------------------------

def _chunk_id(source_name: str, index: int, chunk: str) -> str:
    """Deterministic ID so re-training the same source upserts in place."""
    digest = hashlib.sha1(
        f"{source_name}:{index}:{chunk}".encode("utf-8")
    ).hexdigest()
    return f"{source_name}-{index}-{digest}"



# ---------------------------------------------------------------------------
# Public API — training
# ---------------------------------------------------------------------------

def train_knowledge_base(text_content: str, source_name: str) -> int:
    """
    Chunk `text_content` and store it in the persistent ChromaDB collection.

    No embeddings are computed here — ChromaDB's DefaultEmbeddingFunction
    embeds the raw text chunks itself during `upsert`. Upserting (rather
    than add) makes training idempotent: re-training the same source
    replaces the previous chunks instead of duplicating them.

    Returns the number of chunks written.
    """
    chunks = _chunk_text(text_content)
    if not chunks:
        log.info(
            "train_knowledge_base: no content to train (source=%s)",
            source_name,
        )
        return 0

    collection = _get_collection()

    ids = [_chunk_id(source_name, i, c) for i, c in enumerate(chunks)]
    metadatas = [
        {"source": source_name, "chunk_index": i} for i in range(len(chunks))
    ]

    log.info(
        "train_knowledge_base: upserting %d chunks from source=%s (local embeddings)",
        len(ids),
        source_name,
    )
    collection.upsert(
        ids=ids,
        documents=chunks,
        metadatas=metadatas,
    )

    log.info("train_knowledge_base: stored %d chunks", len(ids))
    return len(ids)


def train_from_file(path: str, source_name: Optional[str] = None) -> int:
    """Convenience: read a UTF-8 text file and feed it to `train_knowledge_base`."""
    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read()
    name = source_name or os.path.basename(path)
    return train_knowledge_base(content, name)



# ---------------------------------------------------------------------------
# Public API — query
# ---------------------------------------------------------------------------

def search_knowledge_base(query: str, n_results: int = 3) -> List[str]:
    """
    Return the top-`n_results` most similar chunks for `query`.

    ChromaDB embeds the query locally with DefaultEmbeddingFunction.
    Returns an empty list if the collection is empty or the query is blank.
    """
    if not query or not query.strip():
        return []

    collection = _get_collection()
    total = collection.count()
    if total == 0:
        return []

    result = collection.query(
        query_texts=[query],
        n_results=min(max(n_results, 1), total),
        include=["documents"],
    )

    documents = result.get("documents") or [[]]
    return list(documents[0]) if documents and documents[0] else []


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def knowledge_base_size() -> int:
    """Return the number of chunks currently stored (0 on any error)."""
    try:
        return _get_collection().count()
    except Exception:
        log.exception("knowledge_base_size failed")
        return 0


def clear_knowledge_base() -> None:
    """Delete every chunk from the collection (does not delete the DB file)."""
    try:
        client = _get_client()
        client.delete_collection(COLLECTION_NAME)
        log.info("clear_knowledge_base: collection %s deleted", COLLECTION_NAME)
    except Exception:
        log.exception("clear_knowledge_base failed")

