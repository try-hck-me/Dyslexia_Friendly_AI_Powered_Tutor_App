"""
Auth / User Management API

Endpoints:
  POST /users/register  — Upsert a user (create or update name/role)
  GET  /users/{user_id} — Look up a user without 404 (returns exists flag)
"""

import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import User
from app.utils.formatter import build_response

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request schemas ────────────────────────────────────────────

class RegisterRequest(BaseModel):
    user_id: str = Field(..., description="Deterministic user ID (e.g. name_slug)")
    name: str = Field(..., min_length=1, description="Display name")
    role: str = Field("student", description="'student' or 'parent'")


# ── POST /users/register ───────────────────────────────────────

@router.post("/users/register")
async def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Upsert a user in SQLite.

    - If the user_id already exists → update name and role.
    - If it doesn't exist → create a new User row.

    This is called by the frontend on every login so the DB always stays
    in sync with the browser's localStorage session.

    Input:  { "user_id": "prashil_kagathara", "name": "Prashil", "role": "student" }
    Output: { "success": true, "data": { "user_id": "...", "name": "...", "created": true/false } }
    """
    try:
        user = db.query(User).filter(User.id == request.user_id).first()
        created = False

        if user:
            # Update name / role in case they changed
            user.name = request.name.strip()
            user.role = request.role
            db.commit()
            logger.info(f"User updated: {request.user_id} ({request.name}, {request.role})")
        else:
            user = User(
                id=request.user_id,
                name=request.name.strip(),
                role=request.role,
            )
            db.add(user)
            db.commit()
            created = True
            logger.info(f"User created: {request.user_id} ({request.name}, {request.role})")

        return build_response(
            success=True,
            data={
                "user_id": user.id,
                "name": user.name,
                "role": user.role,
                "created": created,
            },
        )

    except Exception as e:
        logger.error(f"Register error: {e}")
        # Don't crash the app — return a soft error so frontend degrades gracefully
        return build_response(success=False, error=f"Registration failed: {str(e)}")


# ── GET /users/{user_id} ──────────────────────────────────────

@router.get("/users/{user_id}")
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """
    Look up a user by ID.

    Always returns 200 — never 404. The `exists` flag tells the caller
    whether the user was found. Used by the parent login to verify a
    child's student ID before saving it locally.

    Output: { "success": true, "data": { "user_id": "...", "name": "...", "exists": true/false } }
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return build_response(
            success=True,
            data={"user_id": user.id, "name": user.name, "role": user.role, "exists": True},
        )
    return build_response(
        success=True,
        data={"user_id": user_id, "name": "", "role": "", "exists": False},
    )
