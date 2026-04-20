from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str
    permissions: Optional[dict] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
    permissions: Optional[dict] = None


class PasswordChange(BaseModel):
    current_password: Optional[str] = None
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool = False
    totp_required: bool = False
    totp_setup_required: bool = False


class TOTPSetupResponse(BaseModel):
    secret: str
    qr_uri: str


class TOTPVerifyRequest(BaseModel):
    code: str


class WebsiteCreate(BaseModel):
    url: str
    name: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class WebsiteResponse(BaseModel):
    id: int
    url: str
    name: str
    is_active: bool
    created_at: datetime
    latest_check: Optional[dict] = None

    class Config:
        from_attributes = True


class CheckResultResponse(BaseModel):
    id: int
    website_id: int
    is_up: bool
    status_code: Optional[int]
    latency_ms: Optional[float]
    page_load_time_ms: Optional[float]
    page_size_kb: Optional[float]
    ttfb_ms: Optional[float]
    suggestions: list
    error_message: Optional[str]
    checked_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    username: str
    is_main_admin: bool
    is_active: bool
    totp_enabled: bool
    totp_verified: bool
    permissions: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class WeeklyRoundup(BaseModel):
    avg_latency_change: Optional[float] = None
    avg_speed_change: Optional[float] = None
    uptime_percentage: Optional[float] = None
    total_checks: int = 0
    sites_improved: int = 0
    sites_degraded: int = 0
    tip: str = ""


class DashboardStats(BaseModel):
    total_websites: int = 0
    websites_up: int = 0
    websites_down: int = 0
    avg_latency: Optional[float] = None
    avg_page_load: Optional[float] = None
    uptime_percentage: Optional[float] = None
