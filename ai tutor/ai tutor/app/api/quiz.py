"""
Quiz API — Adaptive quiz generation and submission endpoints.

Endpoints:
  POST /quiz         — Generate adaptive MCQs for a topic
  POST /quiz/submit  — Submit answers and get scored results
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import User, QuizResult
from app.services.quiz_generator import generate_quiz, score_quiz
from app.utils.formatter import build_response

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_TOPIC_LENGTH = 200


# ── Request schemas ────────────────────────────────────────────

class QuizRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    topic: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH,
                       description="Topic for quiz generation")
    num_questions: int = Field(default=5, ge=1, le=10,
                               description="Number of questions (1–10)")


class QuizAnswer(BaseModel):
    question_index: int = Field(..., description="0-based index of the question")
    selected: str = Field(default="", description="Selected answer text")


class QuizSubmitRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    topic: str = Field(..., description="Quiz topic")
    difficulty: str = Field(default="medium", description="Difficulty used during generation")
    questions: list[dict] = Field(..., description="Original quiz questions (from /quiz response)")
    answers: list[QuizAnswer] = Field(..., description="User's submitted answers")


# ── Helper ─────────────────────────────────────────────────────

def _get_or_create_user(user_id: str, db: Session) -> User:
    """
    Fetch user from DB, or create a safe placeholder if missing.
    Avoids NOT NULL violations on name/role columns.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, name=user_id, role="student")
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Auto-created user '{user_id}' from quiz request.")
    return user


# ── POST /quiz ─────────────────────────────────────────────────

@router.post("/quiz")
async def create_quiz(request: QuizRequest, db: Session = Depends(get_db)):
    """
    Generate an adaptive quiz for a given topic.

    Difficulty is chosen automatically based on the user's past scores:
      - Score > 80% on this topic → hard
      - Score < 50% on this topic → easy
      - No history / 50-80% → medium

    The retrieved difficulty is returned in the response so the submit
    endpoint can store it correctly.

    Input:  { "user_id": "prashil", "topic": "photosynthesis", "num_questions": 5 }
    Output: { "success": true, "data": { "questions": [...], "difficulty": "medium", "topic": "..." } }
    """
    try:
        _get_or_create_user(request.user_id, db)

        result = generate_quiz(
            topic=request.topic.strip(),
            user_id=request.user_id,
            db=db,
            num_questions=request.num_questions,
        )

        if "error" in result:
            return build_response(
                success=False,
                error=result["error"],
                data={
                    "difficulty": result.get("difficulty", "medium"),
                    "topic": result.get("topic", request.topic),
                    "questions": [],
                },
            )

        return build_response(
            success=True,
            data={
                "questions": result["questions"],
                "difficulty": result["difficulty"],
                "topic": result["topic"],
                "num_questions": len(result["questions"]),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quiz generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")


# ── POST /quiz/submit ──────────────────────────────────────────

@router.post("/quiz/submit")
async def submit_quiz(request: QuizSubmitRequest, db: Session = Depends(get_db)):
    """
    Submit quiz answers and receive scored results.

    Stores the result in QuizResult with the correct difficulty from
    the generation step (passed back by the frontend).

    Input:  { "user_id": "...", "topic": "...", "difficulty": "medium",
              "questions": [...], "answers": [...] }
    Output: { "success": true, "data": { "score": 4, "total": 5, "percentage": 80.0,
                                         "results": [...] } }
    """
    try:
        _get_or_create_user(request.user_id, db)

        # Score the submission
        answers_dicts = [a.model_dump() for a in request.answers]
        score_result = score_quiz(
            questions=request.questions,
            answers=answers_dicts,
        )

        # Validate difficulty value
        valid_difficulties = {"easy", "medium", "hard"}
        difficulty = request.difficulty if request.difficulty in valid_difficulties else "medium"

        # Persist to database with the actual difficulty used
        quiz_record = QuizResult(
            user_id=request.user_id,
            topic=request.topic.strip(),
            score=score_result["score"],
            total=score_result["total"],
            difficulty=difficulty,
            questions_json=json.dumps(request.questions),
        )
        db.add(quiz_record)
        db.commit()

        return build_response(
            success=True,
            message=f"Quiz submitted! You scored {score_result['score']}/{score_result['total']}.",
            data={
                "score": score_result["score"],
                "total": score_result["total"],
                "percentage": score_result["percentage"],
                "difficulty": difficulty,
                "results": score_result["results"],
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quiz submission error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Quiz submission failed: {str(e)}")
