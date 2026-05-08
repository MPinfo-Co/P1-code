"""Pydantic schemas for fn_expert_setting APIs."""

from __future__ import annotations

from pydantic import BaseModel


class ExpertSettingOut(BaseModel):
    """Response schema for GET /api/expert/settings."""

    is_enabled: bool
    frequency: str
    schedule_time: str | None
    weekday: int | None
    ssb_host: str | None
    ssb_port: int
    ssb_logspace: str | None
    ssb_username: str | None
    ssb_password: str | None

    model_config = {"from_attributes": True}


class ExpertSettingSaveRequest(BaseModel):
    """Request body for PUT /api/expert/settings."""

    is_enabled: bool
    frequency: str
    schedule_time: str | None = None
    weekday: int | None = None
    ssb_host: str
    ssb_port: int
    ssb_logspace: str
    ssb_username: str
    ssb_password: str | None = None


class SsbTestRequest(BaseModel):
    """Request body for POST /api/expert/ssb-test."""

    host: str
    port: int
    logspace: str
    username: str
    password: str
