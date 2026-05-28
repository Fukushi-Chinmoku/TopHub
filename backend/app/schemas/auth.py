from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    login: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=2, max_length=64)


class LoginRequest(BaseModel):
    login: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    login: str
    display_name: str
    rating_avg: float
    rating_count: int
    created_at: datetime


class AuthResponse(BaseModel):
    user: UserOut
