"""
Analytics Engine service.
Computes weak topics, mood trends, and personalized recommendations.
"""

import logging
from datetime import datetime, timedelta, timezone
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.models import ChatHistory, QuizResult, MoodLog

logger = logging.getLogger(__name__)


def get_weak_topics(user_id: str, db: Session, threshold: float = 60.0) -> list[dict]:
    """
    Identify topics where the user scores below threshold.
    
    Returns:
        List of dicts with 'topic', 'avg_score', 'attempts'.
    """
    results = (
        db.query(
            QuizResult.topic,
            func.avg(QuizResult.score * 100.0 / QuizResult.total).label("avg_score"),
            func.count(QuizResult.id).label("attempts"),
        )
        .filter(QuizResult.user_id == user_id, QuizResult.total > 0)
        .group_by(QuizResult.topic)
        .all()
    )

    weak_topics = []
    for row in results:
        avg = round(float(row.avg_score), 1)
        if avg < threshold:
            weak_topics.append({
                "topic": row.topic,
                "avg_score": avg,
                "attempts": row.attempts,
            })

    # Sort by score ascending (weakest first)
    weak_topics.sort(key=lambda x: x["avg_score"])
    return weak_topics


def get_mood_trends(
    user_id: str,
    db: Session,
    days: int = 30,
) -> dict:
    """
    Get mood frequency counts over a time window.
    
    Returns:
        Dict with 'counts', 'total', 'dominant_mood', 'timeline'.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    logs = (
        db.query(MoodLog)
        .filter(MoodLog.user_id == user_id, MoodLog.timestamp >= cutoff)
        .order_by(MoodLog.timestamp.desc())
        .all()
    )

    if not logs:
        return {
            "counts": {"happy": 0, "neutral": 0, "stressed": 0, "frustrated": 0},
            "total": 0,
            "dominant_mood": "neutral",
            "timeline": [],
        }

    mood_counts = Counter(log.mood for log in logs)
    total = len(logs)

    # Ensure all moods present
    for mood in ("happy", "neutral", "stressed", "frustrated"):
        if mood not in mood_counts:
            mood_counts[mood] = 0

    # Timeline (last 10 entries)
    timeline = [
        {
            "mood": log.mood,
            "timestamp": log.timestamp.isoformat() if log.timestamp else "",
        }
        for log in logs[:10]
    ]

    return {
        "counts": dict(mood_counts),
        "total": total,
        "dominant_mood": mood_counts.most_common(1)[0][0],
        "timeline": timeline,
    }


def get_study_stats(user_id: str, db: Session) -> dict:
    """
    Get overall study statistics.

    Returns:
        Dict with questions_asked, quizzes_taken, avg_quiz_score,
        plus profile-page aliases: total_quizzes, average_score,
        streak_days, total_documents.
    """
    questions_asked = (
        db.query(func.count(ChatHistory.id))
        .filter(ChatHistory.user_id == user_id)
        .scalar() or 0
    )

    quiz_stats = (
        db.query(
            func.count(QuizResult.id).label("count"),
            func.avg(QuizResult.score * 100.0 / QuizResult.total).label("avg_score"),
        )
        .filter(QuizResult.user_id == user_id, QuizResult.total > 0)
        .first()
    )

    quizzes_taken = quiz_stats.count if quiz_stats else 0
    avg_score = round(float(quiz_stats.avg_score), 1) if quiz_stats and quiz_stats.avg_score else 0.0

    # Streak: count distinct calendar days with any quiz activity (last 30 days)
    streak_days = _compute_streak(user_id, db)

    # Document count from ChromaDB (best-effort)
    total_documents = _count_documents()

    return {
        # Original field names (kept for backward-compat)
        "questions_asked": questions_asked,
        "quizzes_taken": quizzes_taken,
        "avg_quiz_score": avg_score,
        # Profile-page field names
        "total_quizzes": quizzes_taken,
        "average_score": avg_score,
        "streak_days": streak_days,
        "total_documents": total_documents,
    }


def _compute_streak(user_id: str, db: Session) -> int:
    """Count the number of distinct days with quiz or chat activity (up to 30 days)."""
    from datetime import date
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    quiz_days = {
        r[0].date() if isinstance(r[0], datetime) else r[0]
        for r in db.query(QuizResult.timestamp)
        .filter(QuizResult.user_id == user_id, QuizResult.timestamp >= cutoff)
        .all()
        if r[0]
    }
    chat_days = {
        r[0].date() if isinstance(r[0], datetime) else r[0]
        for r in db.query(ChatHistory.timestamp)
        .filter(ChatHistory.user_id == user_id, ChatHistory.timestamp >= cutoff)
        .all()
        if r[0]
    }
    return len(quiz_days | chat_days)


def _count_documents() -> int:
    """Return the number of unique source documents in ChromaDB (best-effort, 0 on failure)."""
    try:
        from app.services.vector_store import get_raw_chunks_collection
        col = get_raw_chunks_collection()
        count = col.count()
        if count == 0:
            return 0
        result = col.get(limit=min(count, 1000), include=["metadatas"])
        sources = {m.get("source") for m in (result.get("metadatas") or []) if m}
        return len(sources)
    except Exception:
        return 0



def get_recommendations(user_id: str, db: Session) -> list[str]:
    """
    Generate personalized recommendations based on analytics.
    
    Rules:
    - Low quiz score → suggest revision
    - High stress → suggest break
    - No recent activity → encourage studying
    """
    recommendations = []

    # Check weak topics
    weak = get_weak_topics(user_id, db)
    if weak:
        top_weak = weak[0]
        recommendations.append(
            f"📚 Your score in '{top_weak['topic']}' is {top_weak['avg_score']}%. "
            f"Try revising this topic and retaking the quiz."
        )
    
    if len(weak) > 1:
        topics_str = ", ".join(t["topic"] for t in weak[:3])
        recommendations.append(
            f"📖 Topics that need attention: {topics_str}"
        )

    # Check mood trends
    mood_data = get_mood_trends(user_id, db, days=7)
    stressed_count = mood_data["counts"].get("stressed", 0) + mood_data["counts"].get("frustrated", 0)
    
    if stressed_count >= 3:
        recommendations.append(
            "😌 You've been feeling stressed lately. Take a short break, stretch, "
            "or do something fun before studying again."
        )
    elif mood_data["dominant_mood"] == "happy":
        recommendations.append(
            "😊 You're in a great mood! This is a perfect time to tackle challenging topics."
        )

    # Check study activity
    stats = get_study_stats(user_id, db)
    if stats["questions_asked"] == 0:
        recommendations.append(
            "💡 You haven't asked any questions yet. Upload a PDF and start asking!"
        )
    
    if stats["quizzes_taken"] == 0:
        recommendations.append(
            "🧠 Try taking a quiz to test your understanding!"
        )
    elif stats["avg_quiz_score"] > 80:
        recommendations.append(
            "🌟 Great job! Your average score is above 80%. Keep it up!"
        )

    if not recommendations:
        recommendations.append("✅ You're doing well! Keep studying consistently.")

    return recommendations


def get_all_topics(user_id: str, db: Session) -> list[dict]:
    """
    Return every topic the user has attempted, with avg score and attempt count.
    Sorted by avg_score ascending (weakest first) for the bar chart.
    Used by the analytics page to render the full topic performance chart.
    """
    results = (
        db.query(
            QuizResult.topic,
            func.avg(
                QuizResult.score * 100.0 / QuizResult.total
            ).label("avg_score"),
            func.count(QuizResult.id).label("attempts"),
        )
        .filter(QuizResult.user_id == user_id, QuizResult.total > 0)
        .group_by(QuizResult.topic)
        .all()
    )

    topics = [
        {
            "topic": row.topic,
            "avg_score": round(float(row.avg_score or 0), 1),
            "attempts": row.attempts,
        }
        for row in results
    ]

    topics.sort(key=lambda x: x["avg_score"])
    return topics


def get_full_analytics(user_id: str, db: Session) -> dict:
    """
    Get complete analytics dashboard for a user.
    Includes study stats, all topics, weak topics, mood trends, recommendations.
    """
    all_topics = get_all_topics(user_id, db)
    weak_topics = [t for t in all_topics if t["avg_score"] < 60.0]

    return {
        "user_id": user_id,
        "study_stats": get_study_stats(user_id, db),
        "all_topics": all_topics,           # full list for bar chart
        "weak_topics": weak_topics,         # filtered list for recommendations
        "mood_trends": get_mood_trends(user_id, db),
        "recommendations": get_recommendations(user_id, db),
    }
