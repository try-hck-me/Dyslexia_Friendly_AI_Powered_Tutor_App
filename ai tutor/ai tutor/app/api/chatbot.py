"""
Chatbot API — RAG-based study chatbot endpoints.

Endpoints:
  POST /chat               — Ask a question, get an AI answer (saves to history)
  GET  /chat/history/{id}  — Retrieve last N chat messages for a user
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import User, ChatHistory
from app.services.rag_pipeline import ask
from app.utils.formatter import build_response

logger = logging.getLogger(__name__)
router = APIRouter()

# Hard cap: prevent enormous prompts from wasting LLM tokens
MAX_QUESTION_LENGTH = 1_000


# ── Request schemas ────────────────────────────────────────────

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    question: str = Field(..., min_length=1, max_length=MAX_QUESTION_LENGTH,
                          description="Question to ask (max 1,000 characters)")


# ── Helper ─────────────────────────────────────────────────────

def _get_or_create_user(user_id: str, db: Session) -> User:
    """
    Fetch the user from DB, or create a minimal placeholder row if they
    don't exist yet (e.g., user registered while backend was offline).
    Always includes safe defaults for name/role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, name=user_id, role="student")
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Auto-created user '{user_id}' from chat request.")
    return user


# ── POST /chat ─────────────────────────────────────────────────

@router.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    RAG Chatbot — ask a question about uploaded study material.

    Flow:
      1. Ensure user exists in DB (create if missing)
      2. Run Hybrid RAG pipeline (graph + raw chunks → Groq LLM)
      3. Save question + answer to ChatHistory
      4. Return answer, sources, and context flag

    Input:  { "user_id": "prashil", "question": "What is photosynthesis?" }
    Output: { "success": true, "data": { "answer": "...", "sources": [...], "context_found": true } }
    """
    try:
        _get_or_create_user(request.user_id, db)

        # Run RAG pipeline
        result = ask(question=request.question)

        # Derive a short topic label from the first 3 words of the question
        topic = " ".join(request.question.lower().split()[:3])

        # Persist to chat history
        history = ChatHistory(
            user_id=request.user_id,
            question=request.question,
            answer=result["answer"],
            topic=topic,
        )
        db.add(history)
        db.commit()

        return build_response(
            success=True,
            data={
                "answer": result["answer"],
                "sources": result["sources"],
                "context_found": result["context_found"],
                "detail_mode": result.get("detail_mode", False),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# ── GET /chat/history/{user_id} ────────────────────────────────

@router.get("/chat/history/{user_id}")
async def get_chat_history(
    user_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Return the last `limit` chat messages for a user (most recent first).
    Always returns 200 — empty list if no history exists yet.

    Query param: ?limit=20  (default 20, max 100)
    """
    limit = min(max(limit, 1), 100)

    try:
        rows = (
            db.query(ChatHistory)
            .filter(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.timestamp.desc())
            .limit(limit)
            .all()
        )

        history = [
            {
                "id": r.id,
                "question": r.question,
                "answer": r.answer,
                "topic": r.topic,
                "timestamp": r.timestamp.isoformat() if r.timestamp else "",
            }
            for r in rows
        ]

        # Return in chronological order (oldest first) for chat UI rendering
        history.reverse()

        return build_response(
            success=True,
            data={"history": history, "count": len(history)},
        )

    except Exception as e:
        logger.error(f"Chat history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not retrieve history: {str(e)}")
