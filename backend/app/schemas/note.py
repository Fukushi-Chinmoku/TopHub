from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OutlineItem(BaseModel):
    order: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=120)


class NoteCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=500)
    outline: list[OutlineItem] = Field(default_factory=list)
    subject_id: UUID | None = None
    subject_custom: str | None = Field(default=None, max_length=128)
    visibility: str = Field(pattern="^(private|public|group)$")
    group_id: UUID | None = None
    tags: list[str] = Field(default_factory=list, max_length=10)


class NoteUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    outline: list[OutlineItem] | None = None
    subject_id: UUID | None = None
    subject_custom: str | None = Field(default=None, max_length=128)
    visibility: str | None = Field(default=None, pattern="^(private|public|group)$")
    group_id: UUID | None = None
    tags: list[str] | None = Field(default=None, max_length=10)
    content_html: str | None = None


class NoteOut(BaseModel):
    id: UUID
    owner_id: UUID
    owner_login: str | None = None
    owner_display_name: str | None = None
    title: str
    description: str
    outline: list[OutlineItem]
    subject_id: UUID | None
    subject_name: str | None
    subject_custom: str | None
    visibility: str
    group_id: UUID | None
    is_published: bool
    content_html: str | None
    tags: list[str]
    rating_avg: float
    rating_count: int
    created_at: datetime
    updated_at: datetime


class SubjectOut(BaseModel):
    id: UUID
    name: str


class CabinetOut(BaseModel):
    user_id: UUID
    rating_avg: float
    rating_count: int
    notes: list[NoteOut]


class NoteRevisionOut(BaseModel):
    id: UUID
    note_id: UUID
    author_id: UUID | None
    content_html: str
    created_at: datetime
