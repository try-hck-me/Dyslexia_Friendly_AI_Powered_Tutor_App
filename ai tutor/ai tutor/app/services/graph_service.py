"""
Graph RAG orchestration service.
Provides access to the global graph store and hybrid retriever.
"""

import os
import logging
from pathlib import Path
from app.services.graph_rag.store import NetworkXStore
from app.services.graph_rag.engine import HybridRetriever
from app.services.vector_store import get_collection, get_raw_chunks_collection, GRAPH_NODES_COLLECTION, RAW_CHUNKS_COLLECTION
from app.services.embedding import get_model

logger = logging.getLogger(__name__)

# Global instances
_store: NetworkXStore | None = None
_retriever: HybridRetriever | None = None
GRAPH_PATH = Path("data/knowledge_graph.pkl")


def get_store() -> NetworkXStore:
    """Get or initialize the global NetworkXStore."""
    global _store
    if _store is None:
        _store = NetworkXStore()
        if GRAPH_PATH.exists():
            try:
                _store.load_pickle(GRAPH_PATH)
                logger.info(f"Loaded existing knowledge graph with {_store.graph.number_of_nodes()} nodes.")
            except Exception as e:
                logger.error(f"Failed to load knowledge graph: {e}")
    return _store


def reset_store():
    """
    Reset the global store and retriever singletons.
    Called after a new document is uploaded so the retriever is re-initialized
    with the freshly built graph and new ChromaDB data.
    """
    global _store, _retriever
    _store = None
    _retriever = None
    logger.info("Global graph store and retriever reset.")


def get_hybrid_retriever() -> HybridRetriever:
    """Get or initialize the global HybridRetriever with both ChromaDB collections."""
    global _retriever
    if _retriever is None:
        store = get_store()
        graph_nodes_collection = get_collection(GRAPH_NODES_COLLECTION)
        raw_chunks_collection = get_raw_chunks_collection()
        embed_model = get_model()
        _retriever = HybridRetriever(
            store=store,
            graph_nodes_collection=graph_nodes_collection,
            raw_chunks_collection=raw_chunks_collection,
            embed_model=embed_model,
        )
        logger.info(
            f"HybridRetriever initialized. "
            f"Graph nodes: {graph_nodes_collection.count()}, "
            f"Raw chunks: {raw_chunks_collection.count()}"
        )
    return _retriever


def save_global_store():
    """Save the current state of the global store to disk."""
    store = get_store()
    os.makedirs(GRAPH_PATH.parent, exist_ok=True)
    store.save_pickle(GRAPH_PATH)
