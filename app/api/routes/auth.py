from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models import User
from app.schemas.auth import Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: dict = Body(...), db: Session = Depends(get_db)) -> Token:
    if isinstance(payload, dict):
        email = str(payload.get("email") or payload.get("username") or "").strip()
        password = str(payload.get("password") or "")
    else:
        email = str(getattr(payload, "email", None) or getattr(payload, "username", None) or "").strip()
        password = str(getattr(payload, "password", "") or "")
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email/username and password are required",
        )

    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token(str(user.id))
    return Token(access_token=token)
