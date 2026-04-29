"""Globally-used utility helpers (password hashing, request authentication)."""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.db.connector import get_db
from app.db.models import TokenBlacklist

oauth2_scheme = HTTPBearer()


def parse_iso_date(value: str, field: str) -> date:
    """Parse `YYYY-MM-DD`, raising 400 on bad input."""
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field}; expected ISO8601 date (YYYY-MM-DD).",
        ) from exc


@dataclass(frozen=True)
class AuthContext:
    """Resolved identity for an authenticated request."""

    user_id: int
    token: str


def hash_password(password: str) -> str:
    """Compute the SHA-256 hex digest of `password`.

    Args:
        password: The plain-text password to hash.

    Returns:
        str: The 64-character lowercase hex digest of the SHA-256 hash.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(hashed: str, password: str) -> bool:
    """Check whether `password` matches a previously stored SHA-256 digest.

    Uses `hmac.compare_digest` for a constant-time comparison so attackers
    cannot infer the digest one byte at a time from timing differences.

    Args:
        hashed: The stored SHA-256 hex digest produced by `hash_password`.
        password: The plain-text password to verify against `hashed`.

    Returns:
        bool: True if the digests match exactly; False otherwise.
    """
    return hmac.compare_digest(hashed, hash_password(password))


def create_access_token(user_id: int) -> str:
    """Sign a short-lived JWT carrying `sub=user_id` and a fresh `jti`.

    Args:
        user_id: Primary key of the authenticating user.

    Returns:
        str: Encoded JWT signed with the configured HS256 secret.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "jti": uuid4().hex,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def authenticate(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AuthContext:
    """Resolve the calling user's id and bearer token from the request.

    Designed for use as a FastAPI dependency:
    `auth: AuthContext = Depends(authenticate)`. Decodes the JWT, ensures
    its `jti` has not been revoked via `tb_token_blacklist`, and returns
    both the `sub` claim (as `user_id`) and the original token string so
    callers (e.g. logout) can act on the token without re-extracting it.

    Args:
        credentials: Parsed `Authorization: Bearer <token>` header supplied
            by the `HTTPBearer` dependency. The raw JWT lives at
            `credentials.credentials`.
        db: Request-scoped SQLAlchemy session for blacklist lookup.

    Returns:
        AuthContext: The authenticated user's id and the raw bearer token.

    Raises:
        HTTPException: 401 if the token is missing, malformed, expired,
            revoked, or its `sub` claim is not a valid user id.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        sub = payload.get("sub")
        jti = payload.get("jti")
        if sub is None or jti is None:
            raise credentials_error
        user_id = int(sub)
    except (JWTError, ValueError) as exc:
        raise credentials_error from exc

    if db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == jti).first():
        raise credentials_error
    return AuthContext(user_id=user_id, token=token)
