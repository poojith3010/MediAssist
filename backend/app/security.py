import hashlib
import hmac
import time

from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .db import get_db
from .models import User


password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    try:
        return password_hasher.verify(encoded, password)
    except Exception:
        return False


def _token(user_id: int, secret: str) -> str:
    body = f"{user_id}:{int(time.time())}".encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"{body.decode()}.{signature}"


def _user_id(token: str, secret: str) -> int | None:
    try:
        value, signature = token.split(".", 1)
        expected = hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(signature, expected):
            user_id, issued = value.split(":", 1)
            from .config import get_settings
            if time.time() - int(issued) <= get_settings().session_ttl_hours * 3600:
                return int(user_id)
    except (ValueError, TypeError):
        return None
    return None


def create_session(user_id: int, secret: str) -> str:
    return _token(user_id, secret)


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("mediassist_session")
    from .config import get_settings

    user_id = _user_id(token or "", get_settings().app_secret)
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user
