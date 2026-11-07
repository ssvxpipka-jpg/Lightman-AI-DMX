"""
refresh_rag.py — build and query the local Lightman knowledge base.

Usage:
    python -m shared.refresh_rag data/knowledge.txt
    python -m shared.refresh_rag --query "how many channels in a DMX universe"

Store: .lightman_cache/rag (project root). No network. No OpenAI key.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_RAG_DIR = _PROJECT_ROOT / ".lightman_cache" / "rag"

DEFAULT_COLLECTION = "lightman_knowledge"
CHUNK_WORDS = 500
OVERLAP_WORDS = 50
BATCH_SIZE = 64

_TEXT_KEYS = ("text", "content", "body", "knowledge", "description", "value")


def _chunk_text(text: str, chunk_words: int = CHUNK_WORDS, overlap_words: int = OVERLAP_WORDS) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = max(1, chunk_words - overlap_words)
    chunks: list[str] = []
    for start in range(0, len(words), step):
        end = start + chunk_words
        piece = " ".join(words[start:end]).strip()
        if piece:
            chunks.append(piece)
        if end >= len(words):
            break
    return chunks


def _flatten_json(data, stem: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, str):
                out.append((f"{stem}:{i}", item))
            elif isinstance(item, dict):
                name = (item.get("name") or item.get("title") or item.get("id") or f"{stem}:{i}")
                text = None
                for key in _TEXT_KEYS:
                    if isinstance(item.get(key), str):
                        text = item[key]
                        break
                if text is None:
                    text = " | ".join(str(v) for v in item.values() if isinstance(v, (str, int, float)))
                if text.strip():
                    out.append((f"{stem}:{name}", text))
    elif isinstance(data, dict):
        for key in ("documents", "items", "chunks", "entries", "data"):
            if isinstance(data.get(key), list):
                return _flatten_json(data[key], stem)
        for k, v in data.items():
            if isinstance(v, str):
                out.append((f"{stem}:{k}", v))
            elif isinstance(v, (list, dict)):
                out.extend(_flatten_json(v, f"{stem}:{k}"))
    return out


def _read_source(path: Path) -> list[tuple[str, str]]:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace")
        return [(path.stem, text)]
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return _flatten_json(data, path.stem)
    raise ValueError(f"Unsupported source type: {suffix}")


def load_knowledge_base(source_path: str, collection_name: str = DEFAULT_COLLECTION) -> int:
    path = Path(source_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    _RAG_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(_RAG_DIR))
    ef = DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(name=collection_name, embedding_function=ef)
    source_name = path.name
    try:
        collection.delete(where={"source": source_name})
    except Exception:
        pass
    sections = _read_source(path)
    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict] = []
    idx = 0
    for section, text in sections:
        for piece in _chunk_text(text):
            cid = hashlib.sha1(f"{source_name}:{section}:{idx}".encode("utf-8")).hexdigest()[:16]
            ids.append(cid)
            docs.append(piece)
            metas.append({"source": source_name, "section": section, "chunk_index": idx})
            idx += 1
    if not ids:
        return 0
    for start in range(0, len(ids), BATCH_SIZE):
        collection.add(
            ids=ids[start:start + BATCH_SIZE],
            documents=docs[start:start + BATCH_SIZE],
            metadatas=metas[start:start + BATCH_SIZE],
        )
    return len(ids)


def query_knowledge_base(query: str, n_results: int = 3, collection_name: str = DEFAULT_COLLECTION) -> list[dict]:
    if not query or not query.strip():
        return []
    if not _RAG_DIR.exists():
        return []
    client = chromadb.PersistentClient(path=str(_RAG_DIR))
    ef = DefaultEmbeddingFunction()
    try:
        collection = client.get_collection(name=collection_name, embedding_function=ef)
    except Exception:
        return []
    res = collection.query(query_texts=[query], n_results=n_results)
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    return [{"text": d, "metadata": m or {}} for d, m in zip(docs, metas)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build or query the Lightman knowledge base.")
    ap.add_argument("source", nargs="?", help="Path to .txt or .json knowledge file")
    ap.add_argument("--collection", default=DEFAULT_COLLECTION)
    ap.add_argument("--query", help="Query the collection instead of loading")
    ap.add_argument("--n", type=int, default=3)
    args = ap.parse_args(argv)
    if args.query:
        hits = query_knowledge_base(args.query, n_results=args.n, collection_name=args.collection)
        if not hits:
            print("No results.")
            return 0
        for i, h in enumerate(hits, 1):
            meta = h["metadata"]
            print(f"[{i}] {meta.get('source', '?')} / {meta.get('section', '?')}")
            print(h["text"][:400])
            print("-" * 40)
        return 0
    if not args.source:
        ap.error("source path is required unless --query is used")
    n = load_knowledge_base(args.source, collection_name=args.collection)
    print(f"Loaded {n} chunks into '{args.collection}' from {args.source}")
    return 0


if __name__ == "__main__":
    sys.exit(main())