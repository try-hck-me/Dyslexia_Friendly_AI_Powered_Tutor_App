"""
Embedding service using Sentence Transformers.
Singleton pattern to avoid reloading the model on every request.
"""

import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Singleton model instance
_model: SentenceTransformer | None = None
MODEL_NAME = "all-MiniLM-L6-v2"


def get_model() -> SentenceTransformer:
    """Get or initialize the embedding model (singleton)."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model loaded successfully.")
    return _model


def embed_text(text: str) -> list[float]:
    """
    Generate embedding vector for a single text string.
    
    Args:
        text: Input text to embed.
        
    Returns:
        List of floats representing the embedding vector.
    """
    model = get_model()
    embedding = model.encode(text, show_progress_bar=False)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embedding vectors for multiple texts (batch).
    
    Args:
        texts: List of input texts.
        
    Returns:
        List of embedding vectors.
    """
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False, batch_size=32)
    return embeddings.tolist()
