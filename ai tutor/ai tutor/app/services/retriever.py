"""
Retriever service.
Orchestrates embedding + vector search to find relevant chunks.
"""

from app.services.vector_store import query_documents


def retrieve_chunks(
    query: str,
    top_k: int = 4,
) -> list[dict]:
    """
    Retrieve the most relevant text chunks for a given query.
    
    Args:
        query: User's question or search query.
        top_k: Number of chunks to retrieve.
        
    Returns:
        List of chunk dicts with 'text', 'source', 'distance'.
    """
    results = query_documents(query_text=query, n_results=top_k)
    return results


def retrieve_chunks_as_text(
    query: str,
    top_k: int = 4,
) -> str:
    """
    Retrieve relevant chunks and join them as a single context string.
    
    Args:
        query: User's question.
        top_k: Number of chunks to retrieve.
        
    Returns:
        Concatenated text from retrieved chunks.
    """
    chunks = retrieve_chunks(query, top_k)
    if not chunks:
        return ""
    return "\n\n---\n\n".join(chunk["text"] for chunk in chunks)
