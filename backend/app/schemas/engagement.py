from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CommentCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=3000)


class CommentOut(BaseModel):
    id: UUID
    note_id: UUID
    user_id: UUID
    login: str
    display_name: str
    content: str
    created_at: datetime


class RatingRequest(BaseModel):
    score: int = Field(ge=1, le=5)


class RatingOut(BaseModel):
    note_id: UUID
    rating_avg: float
    rating_count: int
    my_score: int | None
