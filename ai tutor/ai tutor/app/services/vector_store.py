"""
ChromaDB vector store service.
Handles storing and querying document embeddings.

Two collections are maintained:
  - GRAPH_NODES_COLLECTION: embeddings of extracted graph concept nodes
  - RAW_CHUNKS_COLLECTION:  embeddings of raw text chunks (lossless fallback)
"""

from typing import Any

import os
import logging
import chromadb
from app.services.embedding import embed_texts, embed_text

logger = logging.getLogger(__name__)

# Persistent ChromaDB storage
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")
os.makedirs(CHROMA_DIR, exist_ok=True)

# Singleton client
_client: Any | None = None

# Collection names
GRAPH_NODES_COLLECTION = "graph_concept_nodes"   # graph node embeddings
RAW_CHUNKS_COLLECTION = "raw_study_chunks"        # raw chunk embeddings (lossless)

# Legacy alias (kept for any code that still imports COLLECTION_NAME)
COLLECTION_NAME = GRAPH_NODES_COLLECTION


def get_client() -> Any:
    """Get or initialize the ChromaDB persistent client."""
    global _client
    if _client is None:
        logger.info(f"Initializing ChromaDB at: {CHROMA_DIR}")
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _client


def get_collection(name: str = GRAPH_NODES_COLLECTION) -> chromadb.Collection:
    """Get or create a ChromaDB collection."""
    client = get_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def get_raw_chunks_collection() -> chromadb.Collection:
    """Get or create the raw-chunks ChromaDB collection."""
    return get_collection(RAW_CHUNKS_COLLECTION)


# ──────────────────────────────────────────
# Graph Node Store / Query
# ──────────────────────────────────────────

def add_documents(
    chunks: list[str],
    metadatas: list[dict] | None = None,
    source: str = "unknown",
) -> int:
    """
    Add document chunks (graph node texts) to the graph nodes vector store.

    Args:
        chunks: List of text chunks.
        metadatas: Optional metadata for each chunk.
        source: Source identifier.

    Returns:
        Number of chunks added.
    """
    if not chunks:
        return 0

    collection = get_collection(GRAPH_NODES_COLLECTION)
    embeddings = embed_texts(chunks)
    existing_count = collection.count()
    ids = [f"{source}_{existing_count + i}" for i in range(len(chunks))]

    if metadatas is None:
        metadatas = [{"source": source, "chunk_index": i} for i in range(len(chunks))]

    collection.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)
    logger.info(f"Added {len(chunks)} graph-node chunks from '{source}'.")
    return len(chunks)


def query_documents(
    query_text: str,
    n_results: int = 4,
) -> list[dict]:
    """
    Query the graph nodes collection for similar documents.

    Returns:
        List of dicts with 'text', 'source', 'distance' keys.
    """
    collection = get_collection(GRAPH_NODES_COLLECTION)
    if collection.count() == 0:
        return []

    query_embedding = embed_text(query_text)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    documents = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            raw_metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            metadata = raw_metadata if raw_metadata is not None else {}
            distance = results["distances"][0][i] if results["distances"] else 0.0
            documents.append({
                "text": doc,
                "source": metadata.get("source", "unknown"),
                "chunk_index": metadata.get("chunk_index", 0),
                "distance": distance,
            })
    return documents


def get_document_count() -> int:
    """Get the total number of documents in the graph nodes store."""
    return get_collection(GRAPH_NODES_COLLECTION).count()


# ──────────────────────────────────────────
# Raw Chunk Store / Query (lossless fallback)
# ──────────────────────────────────────────

def add_raw_chunks(
    chunks: list[dict],
) -> int:
    """
    Embed and store raw text chunks in the raw_study_chunks collection.

    Args:
        chunks: List of dicts with 'text', 'source', 'chunk_index' keys.

    Returns:
        Number of chunks stored.
    """
    if not chunks:
        return 0

    collection = get_raw_chunks_collection()

    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    # Use source+chunk_index as stable IDs; upsert so re-uploading same file replaces old data
    ids = [f"{c.get('source', 'unknown')}_raw_{c.get('chunk_index', i)}" for i, c in enumerate(chunks)]
    metadatas = [
        {
            "source": c.get("source", "unknown"),
            "chunk_index": c.get("chunk_index", i),
            "heading": c.get("heading", ""),
        }
        for i, c in enumerate(chunks)
    ]

    # Upsert in batches
    batch_size = 100
    for start in range(0, len(ids), batch_size):
        end = min(start + batch_size, len(ids))
        collection.upsert(
            ids=ids[start:end],
            documents=texts[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )

    logger.info(f"Stored {len(chunks)} raw chunks in '{RAW_CHUNKS_COLLECTION}'.")
    return len(chunks)


def query_raw_chunks(
    query_text: str,
    n_results: int = 5,
) -> list[dict]:
    """
    Query the raw chunks collection for the most relevant passages.

    Returns:
        List of dicts with 'text', 'source', 'heading', 'distance' keys.
    """
    collection = get_raw_chunks_collection()
    if collection.count() == 0:
        return []

    query_embedding = embed_text(query_text)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    documents = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            raw_metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            metadata = raw_metadata if raw_metadata is not None else {}
            distance = results["distances"][0][i] if results["distances"] else 0.0
            documents.append({
                "text": doc,
                "source": metadata.get("source", "unknown"),
                "heading": metadata.get("heading", ""),
                "distance": distance,
            })
    return documents


def get_raw_chunk_count() -> int:
    """Get the total number of raw chunks stored."""
    return get_raw_chunks_collection().count()
