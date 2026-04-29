"""Pydantic schemas for /auth endpoints."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Credentials submitted to `POST /auth/login`."""

    email: EmailStr = Field(..., description="Registered user email.")
    password: str = Field(..., min_length=1, description="Plain-text password.")


class LoginResponse(BaseModel):
    """Token returned after a successful login."""

    access_token: str = Field(..., description="Signed JWT access token.")
    token_type: str = Field("bearer", description="Auth scheme — always 'bearer'.")
    user_id: int = Field(..., description="Authenticated user's id.")


class LogoutResponse(BaseModel):
    """Result of `POST /auth/logout`."""

    detail: str = Field("Logged out", description="Human-readable status.")
