from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    login: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    rating_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    owned_groups = relationship("Group", foreign_keys="Group.owner_id", cascade="all, delete-orphan")
    group_memberships = relationship("GroupMembership", back_populates="user", cascade="all, delete-orphan")
    friendships_sent = relationship(
        "Friendship",
        foreign_keys="Friendship.requester_id",
        back_populates="requester",
        cascade="all, delete-orphan",
    )
    friendships_received = relationship(
        "Friendship",
        foreign_keys="Friendship.addressee_id",
        back_populates="addressee",
        cascade="all, delete-orphan",
    )
    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")
    comments = relationship("NoteComment", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("NoteRating", back_populates="user", cascade="all, delete-orphan")
    revisions = relationship("NoteRevision")
