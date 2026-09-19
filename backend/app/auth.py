"""
Authentication helpers: password hashing (bcrypt) and JWT issuing/verifying.
Kept isolated from the route handlers so it can be unit-tested on its own.
"""
import datetime
from typing import Optional

import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models

# Using the `bcrypt` library directly rather than passlib's CryptContext
# wrapper. passlib is effectively unmaintained and has a known breaking
# incompatibility with bcrypt>=4.1 (it looks for a removed __about__
# attribute), which crashes every hash/verify call on any environment
# that has a recent bcrypt installed. Calling bcrypt directly avoids that
# entirely and has one job to do.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# bcrypt has a hard 72-byte input limit -- longer passwords are truncated
# safely here rather than raising an error the user wouldn't understand.
_MAX_BCRYPT_BYTES = 72


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")[:_MAX_BCRYPT_BYTES]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pw_bytes = plain.encode("utf-8")[:_MAX_BCRYPT_BYTES]
    return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))


def create_access_token(subject: str, role: str = "analyst") -> str:
    expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )
    # role rides along in the token so the frontend can render admin-only
    # UI (resolve buttons, site registration) without a separate /auth/me
    # round-trip. The token is still validated against the DB on every
    # protected request, so this claim is a convenience, not a gate.
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = decode_access_token(token)
    if email is None:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def get_current_site(
    x_api_key: str = Header(..., description="The monitored site's API key"),
    db: Session = Depends(get_db),
) -> models.Site:
    """
    Authenticates an EXTERNAL website sending events -- not a dashboard
    user. Deliberately separate from JWT auth: a monitored website's
    backend shouldn't need a BinduParakh login, just its own API key,
    exactly like how most real ingestion APIs (Stripe, Sentry, etc.) work.
    """
    site = db.query(models.Site).filter(models.Site.api_key == x_api_key).first()
    if not site:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return site
