"""
Graph Visualization API.
"""

import logging
from fastapi import APIRouter
from app.services.graph_service import get_store, reset_store
from app.utils.formatter import build_response

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/graph/viz")
async def get_graph_viz():
    """
    Get graph nodes and edges formatted for visualization (streamlit-agraph).
    """
    try:
        store = get_store()
        nodes, edges = store.get_nodes_for_viz()
        
        return build_response(
            success=True,
            data={
                "nodes": nodes,
                "edges": edges,
                "count": {
                    "nodes": len(nodes),
                    "edges": len(edges)
                }
            }
        )
    except Exception as e:
        logger.error(f"Failed to fetch graph for visualization: {e}")
        return build_response(
            success=False,
            message=str(e),
            data={"nodes": [], "edges": []}
        )


@router.post("/graph/reload")
async def reload_graph():
    """Force reload the knowledge graph from disk."""
    try:
        reset_store()
        store = get_store()
        nodes, edges = store.get_nodes_for_viz()
        return build_response(
            success=True,
            data={"nodes": len(nodes), "edges": len(edges)},
            message=f"Graph reloaded: {len(nodes)} nodes, {len(edges)} edges",
        )
    except Exception as e:
        logger.error(f"Failed to reload graph: {e}")
        return build_response(success=False, message=str(e))