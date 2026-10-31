"""
FriendlyBot API — Emotional support chatbot endpoint.

Enhanced with optional topic-awareness: if the student mentions a study topic,
a brief context snippet is fetched from the hybrid retriever to make the
FriendlyBot response feel more personally relevant.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import json
from app.database.db import get_db
from app.database.models import User, MoodLog
from app.services.sentiment import detect_mood
from app.services.llm_groq import generate
from app.utils.prompts import (
    FRIENDLY_SYSTEM_PROMPT,
    FRIENDLY_USER_PROMPT,
    FRIENDLY_SYSTEM_PROMPT_WITH_CONTEXT,
    FRIENDLY_USER_PROMPT_WITH_CONTEXT,
)
from app.utils.formatter import build_response

logger = logging.getLogger(__name__)
router = APIRouter()

# Keywords that suggest the student is talking about a study topic
_STUDY_KEYWORDS = {
    "understand", "learn", "study", "chapter", "topic", "lesson", "exam",
    "test", "question", "confused", "stuck", "explain", "homework", "notes",
    "acid", "base", "cell", "force", "energy", "atom", "equation", "formula",
    "biology", "chemistry", "physics", "math", "history", "english", "science",
    "concept", "definition", "solve", "calculate", "answer", "wrong", "mistake",
    "difficult", "hard", "easy", "remember", "forgot", "forget",
}


def _message_has_study_topic(message: str) -> bool:
    """Check if the message contains any study-related keywords."""
    words = set(message.lower().split())
    return bool(words & _STUDY_KEYWORDS)


def _fetch_brief_context(message: str) -> str:
    """
    Try to fetch a brief (max 300 char) context snippet from the hybrid retriever.
    Returns empty string if retriever is not ready or fails.
    """
    try:
        from app.services.graph_service import get_hybrid_retriever
        from app.services.graph_rag.engine import HybridRetrieverNotReadyError
        retriever = get_hybrid_retriever()
        context, _ = retriever.retrieve(message, top_k=2, hops=1)
        # Trim to first 300 chars to keep FriendlyBot response focused
        if context:
            return context[:300].strip() + ("..." if len(context) > 300 else "")
    except Exception:
        pass
    return ""


class FriendlyRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    message: str = Field(..., min_length=1, description="User's message")


@router.post("/friendly")
async def friendly_chat(request: FriendlyRequest, db: Session = Depends(get_db)):
    """
    FriendlyBot emotional support endpoint.

    - Detects user mood via sentiment analysis
    - If message contains a study topic, fetches a brief context snippet
    - Generates warm, encouraging, and contextually aware response
    - Logs mood to database

    Input: { "user_id": "1", "message": "I feel stressed about acids and bases" }
    """
    try:
        # Ensure user exists — create a safe placeholder if missing
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            user = User(id=request.user_id, name=request.user_id, role="student")
            db.add(user)
            db.commit()
            logger.info(f"Auto-created user '{request.user_id}' from friendly request.")

        # Step 1: Detect mood
        mood_json = detect_mood(request.message)
        mood_str = mood_json.get("detected_emotion", "neutral")

        # Step 2: Check for study-topic keywords and fetch optional context
        study_context = ""
        use_context_prompt = False
        if _message_has_study_topic(request.message):
            study_context = _fetch_brief_context(request.message)
            use_context_prompt = bool(study_context)

        # Step 3: Build prompt (with or without context)
        if use_context_prompt:
            user_prompt = FRIENDLY_USER_PROMPT_WITH_CONTEXT.format(
                mood_json=json.dumps(mood_json, indent=2),
                message=request.message,
                context=study_context,
            )
            system_prompt = FRIENDLY_SYSTEM_PROMPT_WITH_CONTEXT
        else:
            user_prompt = FRIENDLY_USER_PROMPT.format(
                mood_json=json.dumps(mood_json, indent=2),
                message=request.message,
            )
            system_prompt = FRIENDLY_SYSTEM_PROMPT

        # Step 4: Generate response
        response_text = generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=350,
        )

        # Step 5: Log mood to database
        mood_log = MoodLog(
            user_id=request.user_id,
            mood=mood_str,
            message=request.message,
            response=response_text,
        )
        db.add(mood_log)
        db.commit()

        return build_response(
            success=True,
            data={
                "mood": mood_str,
                "response": response_text,
            },
        )

    except Exception as e:
        logger.error(f"FriendlyBot error: {e}")
        raise HTTPException(status_code=500, detail=f"FriendlyBot failed: {str(e)}")
