"""/auth router — issue and revoke JWT access tokens."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session

from app.logger_utils import get_system_logger
from app.api.schema.auth import LoginRequest, LoginResponse, LogoutResponse
from app.config.settings import settings
from app.db.connector import get_db
from app.db.models.user_role import TokenBlacklist, User
from app.utils.util_store import (
    AuthContext,
    authenticate,
    create_access_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
system_logger = get_system_logger()


@router.post("/login", response_model=LoginResponse)
def login(login_req: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Authenticate `email` + `password` and return a JWT access token."""
    system_logger.info(f"User with Email: {login_req.email} attempt to login")
    user = db.query(User).filter(User.email == login_req.email).first()
    if user is None or not verify_password(user.password_hash, login_req.password):
        system_logger.warning("Error Email input")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    system_logger.info(f"User with Email: {login_req.email} successfully logged in")
    return LoginResponse(access_token=create_access_token(user.id), user_id=user.id)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    auth: AuthContext = Depends(authenticate),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    """Revoke the caller's JWT by recording its `jti` in `tb_token_blacklist`."""
    payload = jwt.decode(
        auth.token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    jti = payload["jti"]
    exp = payload["exp"]

    if db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == jti).first():
        return LogoutResponse(detail="JWT expired")

    db.add(
        TokenBlacklist(
            token_jti=jti,
            expired_at=datetime.fromtimestamp(exp, tz=timezone.utc).replace(
                tzinfo=None
            ),
            updated_by=auth.user_id,
        )
    )
    db.commit()
    return LogoutResponse(detail="Logged out")
