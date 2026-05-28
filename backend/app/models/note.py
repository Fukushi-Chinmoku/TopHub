from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    outline: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    subject_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
    )
    subject_custom: Mapped[str | None] = mapped_column(String(128), nullable=True)
    visibility: Mapped[str] = mapped_column(String(16), nullable=False, default="private")
    group_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    content_yjs: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    owner = relationship("User", back_populates="notes")
    subject = relationship("Subject", back_populates="notes")
    tags = relationship("NoteTag", back_populates="note", cascade="all, delete-orphan")
    comments = relationship("NoteComment", back_populates="note", cascade="all, delete-orphan")
    ratings = relationship("NoteRating", back_populates="note", cascade="all, delete-orphan")
    revisions = relationship("NoteRevision", back_populates="note", cascade="all, delete-orphan")


class NoteTag(Base):
    __tablename__ = "note_tags"
    __table_args__ = (UniqueConstraint("note_id", "tag", name="uq_note_tag"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    note_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    tag: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    note = relationship("Note", back_populates="tags")
