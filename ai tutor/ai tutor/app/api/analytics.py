"""
Analytics API — User analytics and recommendations endpoint.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import User
from app.services.analytics_engine import get_full_analytics
from app.utils.formatter import build_response

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/analytics/{user_id}")
async def get_analytics(user_id: str, db: Session = Depends(get_db)):
    """
    Get full analytics dashboard for a user.

    If the user doesn't exist yet, auto-creates them and returns
    empty analytics (no 404). This ensures the dashboard always
    loads cleanly on first visit after login.

    Returns:
    - Study stats (questions asked, quizzes taken, avg score)
    - Weak topics (topics with low quiz scores)
    - Mood trends (mood frequency over last 30 days)
    - Personalized recommendations
    """
    try:
        # Auto-create user if not in DB yet (graceful — no 404)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id, name=user_id, role="student")
            db.add(user)
            db.commit()
            logger.info(f"Analytics: auto-created user '{user_id}'")

        analytics = get_full_analytics(user_id=user_id, db=db)

        return build_response(
            success=True,
            data=analytics,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

