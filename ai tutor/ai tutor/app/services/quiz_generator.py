"""
Quiz Generator service.
Generates adaptive MCQs from context using the Groq LLM.
Now uses the HybridRetriever for rich, chapter-spanning context.
"""

import logging
from sqlalchemy.orm import Session
from app.services.llm_groq import generate
from app.services.graph_service import get_hybrid_retriever
from app.services.graph_rag.engine import HybridRetrieverNotReadyError
from app.utils.prompts import QUIZ_SYSTEM_PROMPT, QUIZ_GENERATION_PROMPT, DIFFICULTY_INSTRUCTIONS
from app.utils.formatter import parse_quiz_json
from app.database.models import QuizResult

logger = logging.getLogger(__name__)


def determine_difficulty(user_id: str, topic: str, db: Session) -> str:
    """
    Determine quiz difficulty based on past performance.

    Rules:
    - Score > 80% → hard
    - Score < 50% → easy
    - Otherwise → medium
    - No history → medium
    """
    recent_results = (
        db.query(QuizResult)
        .filter(QuizResult.user_id == user_id, QuizResult.topic == topic)
        .order_by(QuizResult.timestamp.desc())
        .limit(5)
        .all()
    )

    if not recent_results:
        return "medium"

    total_score = sum(r.score for r in recent_results)
    total_possible = sum(r.total for r in recent_results)

    if total_possible == 0:
        return "medium"

    avg_percentage = (total_score / total_possible) * 100

    if avg_percentage > 80:
        return "hard"
    elif avg_percentage < 50:
        return "easy"
    return "medium"


def generate_quiz(
    topic: str,
    user_id: str,
    db: Session,
    num_questions: int = 5,
) -> dict:
    """
    Generate a quiz with adaptive difficulty using hybrid retrieval.

    Args:
        topic: The topic to generate questions about.
        user_id: User ID for difficulty adaptation.
        db: Database session.
        num_questions: Number of questions.

    Returns:
        Dict with 'questions', 'difficulty', 'topic'.
    """
    # Step 1: Determine difficulty
    difficulty = determine_difficulty(user_id, topic, db)
    difficulty_instruction = DIFFICULTY_INSTRUCTIONS.get(difficulty, "")

    # Step 2: Retrieve context using HybridRetriever
    # (same rich context path as the chatbot — graph + raw chunks)
    context = ""
    try:
        retriever = get_hybrid_retriever()
        context, _ = retriever.retrieve(question=topic, top_k=3, hops=1)
    except HybridRetrieverNotReadyError:
        return {
            "questions": [],
            "difficulty": difficulty,
            "topic": topic,
            "error": "No study material found. Please upload a PDF first.",
        }
    except Exception as e:
        logger.warning(f"Hybrid retrieval failed for quiz, error: {e}")
        context = ""

    if not context or not context.strip():
        return {
            "questions": [],
            "difficulty": difficulty,
            "topic": topic,
            "error": "No relevant content found for this topic. Try a broader topic or upload more study material.",
        }

    # Step 3: Build prompt
    # Truncate context to ~4 000 chars (~1 000 tokens) so the full request
    # stays well under Groq's 12 000 TPM limit on the free tier.
    MAX_CONTEXT_CHARS = 4000
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n[...content truncated for length...]"

    prompt = QUIZ_GENERATION_PROMPT.format(
        num_questions=num_questions,
        difficulty=difficulty,
        difficulty_instruction=difficulty_instruction,
        context=context,
    )

    # Step 4: Generate via LLM
    raw_response = generate(
        user_prompt=prompt,
        system_prompt=QUIZ_SYSTEM_PROMPT,
        temperature=0.5,
        max_tokens=1500,
    )

    # Step 5: Parse JSON response
    questions = parse_quiz_json(raw_response)

    if not questions:
        logger.warning(f"Failed to parse quiz JSON. Raw response: {raw_response[:200]}")
        return {
            "questions": [],
            "difficulty": difficulty,
            "topic": topic,
            "error": "Failed to generate quiz. Please try again.",
        }

    return {
        "questions": questions,
        "difficulty": difficulty,
        "topic": topic,
    }


def score_quiz(
    questions: list[dict],
    answers: list[dict],
) -> dict:
    """
    Score a submitted quiz.

    Args:
        questions: Original quiz questions.
        answers: User's answers [{"question_index": 0, "selected": "Option A"}]

    Returns:
        Dict with 'score', 'total', 'percentage', 'results'.
    """
    score = 0
    total = len(questions)
    results = []

    # Build answer lookup by question_index
    answer_map = {a.get("question_index", i): a.get("selected", "") for i, a in enumerate(answers)}

    for i, question in enumerate(questions):
        correct = question.get("answer", "")
        selected = answer_map.get(i, "")
        is_correct = selected.strip().lower() == correct.strip().lower()

        if is_correct:
            score += 1

        results.append({
            "question_index": i,
            "question": question.get("question", ""),
            "correct": correct,
            "selected": selected,
            "is_correct": is_correct,
            "explanation": question.get("explanation", ""),
        })

    return {
        "score": score,
        "total": total,
        "percentage": round((score / total) * 100, 1) if total > 0 else 0,
        "results": results,
    }
