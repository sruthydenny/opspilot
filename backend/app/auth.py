import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import AuthSession, User


security = HTTPBearer()

SESSION_DURATION_HOURS = 24


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    )

    return f"{salt}${password_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    salt, expected_hash = stored_hash.split("$", 1)

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()

    return secrets.compare_digest(actual_hash, expected_hash)


def create_session(db: Session, user_id: int) -> str:
    token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    session = AuthSession(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.utcnow()
        + timedelta(hours=SESSION_DURATION_HOURS),
    )

    db.add(session)
    db.commit()

    return token


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    session = (
        db.query(AuthSession)
        .filter(AuthSession.token_hash == token_hash)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token.",
        )

    if session.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=401,
            detail="Authentication session expired.",
        )

    user = db.query(User).filter(User.id == session.user_id).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found.",
        )

    return user