"""
AI Tutor — Dyslexia-Friendly Learning Assistant
Main FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.db import init_db
from app.api import upload, chatbot, friendlybot, quiz, analytics, graph, tts, auth
from app.services.graph_service import get_store
import os
from fastapi.staticfiles import StaticFiles

# ─── Logging ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Lifespan (startup / shutdown) ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all resources on startup."""
    logger.info("=" * 60)
    logger.info("  AI TUTOR — Dyslexia-Friendly Learning Assistant")
    logger.info("=" * 60)

    # 1. SQLite tables + safe migration for new columns
    init_db()
    logger.info("✅ Database initialized.")

    # 2. Knowledge Graph from disk (non-blocking if missing)
    try:
        get_store()
        logger.info("✅ Knowledge Graph loaded.")
    except Exception as e:
        logger.warning(f"⚠️  Knowledge Graph not loaded: {e}")

    logger.info("✅ Server is ready. Visit /docs for API documentation.")
    logger.info("=" * 60)

    yield

    logger.info("Server shutting down…")


# ─── FastAPI App ────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Tutor — Dyslexia-Friendly Learning Assistant",
    description=(
        "Production-ready AI backend for dyslexia-friendly learning. "
        "Features: RAG Chatbot, Emotional Support (FriendlyBot), "
        "Adaptive Quiz Generator, Knowledge Graph, Analytics, and TTS."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# ─── CORS ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static Files ───────────────────────────────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

# ─── Routers ────────────────────────────────────────────────────────────
app.include_router(auth.router,        prefix="", tags=["👤 Auth"])
app.include_router(upload.router,      prefix="", tags=["📄 Upload"])
app.include_router(chatbot.router,     prefix="", tags=["🤖 Chatbot"])
app.include_router(friendlybot.router, prefix="", tags=["❤️ FriendlyBot"])
app.include_router(quiz.router,        prefix="", tags=["🧠 Quiz"])
app.include_router(analytics.router,   prefix="", tags=["📊 Analytics"])
app.include_router(graph.router,       prefix="", tags=["🕸️ Graph"])
app.include_router(tts.router,         prefix="", tags=["🔊 TTS"])


# ─── Health Check ───────────────────────────────────────────────────────
@app.get("/", tags=["🏥 Health"])
async def health_check():
    """Basic health check — confirms the server is running."""
    return {
        "status": "healthy",
        "service": "AI Tutor — Dyslexia-Friendly Learning Assistant",
        "version": "2.0.0",
    }


@app.get("/status", tags=["🏥 Health"])
async def full_status():
    """
    Detailed status check — reports the health of all subsystems:
    SQLite DB, ChromaDB (both collections), and the Knowledge Graph.
    """
    from app.database.db import SessionLocal
    from app.services.vector_store import get_raw_chunks_collection, get_collection, GRAPH_NODES_COLLECTION
    from app.services.graph_service import get_store as _get_store

    components: dict = {}

    # 1. SQLite
    try:
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
        components["sqlite"] = {"status": "ok"}
    except Exception as e:
        components["sqlite"] = {"status": "error", "detail": str(e)}

    # 2. ChromaDB — raw chunks
    try:
        raw = get_raw_chunks_collection()
        components["chroma_raw_chunks"] = {"status": "ok", "count": raw.count()}
    except Exception as e:
        components["chroma_raw_chunks"] = {"status": "error", "detail": str(e)}

    # 3. ChromaDB — graph nodes
    try:
        nodes = get_collection(GRAPH_NODES_COLLECTION)
        components["chroma_graph_nodes"] = {"status": "ok", "count": nodes.count()}
    except Exception as e:
        components["chroma_graph_nodes"] = {"status": "error", "detail": str(e)}

    # 4. Knowledge Graph
    try:
        store = _get_store()
        n_nodes = store.graph.number_of_nodes()
        n_edges = store.graph.number_of_edges()
        components["knowledge_graph"] = {
            "status": "ok",
            "nodes": n_nodes,
            "edges": n_edges,
        }
    except Exception as e:
        components["knowledge_graph"] = {"status": "error", "detail": str(e)}

    overall = "healthy" if all(v["status"] == "ok" for v in components.values()) else "degraded"

    return {
        "status": overall,
        "version": "2.0.0",
        "components": components,
    }
