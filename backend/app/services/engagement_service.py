from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.comment import NoteComment
from app.models.note import Note
from app.models.rating import NoteRating
from app.models.user import User
from app.services.access_policy import AccessPolicy
from app.services.note_service import NoteService


class EngagementService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.note_service = NoteService(db)
        self.policy = AccessPolicy(db)

    async def add_comment(self, user: User, note_id: UUID, content: str) -> NoteComment:
        note = await self.note_service.get_note_for_viewer(user, note_id)
        if not await self.policy.can_comment(user.id, note):
            raise ValueError("Comments are available only for published notes")

        text = content.strip()
        if not text:
            raise ValueError("Comment cannot be empty")

        comment = NoteComment(note_id=note.id, user_id=user.id, content=text)
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return await self.get_comment(comment.id)

    async def list_comments(self, user: User, note_id: UUID) -> list[NoteComment]:
        note = await self.note_service.get_note_for_viewer(user, note_id)
        if not await self.policy.can_comment(user.id, note):
            return []
        result = await self.db.scalars(
            select(NoteComment)
            .options(joinedload(NoteComment.user))
            .where(NoteComment.note_id == note.id)
            .order_by(NoteComment.created_at.asc())
        )
        return list(result.all())

    async def rate_note(self, user: User, note_id: UUID, score: int) -> tuple[Note, int | None]:
        note = await self.note_service.get_note_for_viewer(user, note_id)
        if not note.is_published:
            raise ValueError("Ratings are available only for published notes")
        if not await self.policy.can_rate(user.id, note):
            raise ValueError("Нельзя оценивать собственный конспект")

        rating = await self.db.scalar(
            select(NoteRating).where(
                NoteRating.note_id == note.id,
                NoteRating.user_id == user.id,
            )
        )
        if rating is None:
            rating = NoteRating(note_id=note.id, user_id=user.id, score=score)
            self.db.add(rating)
        else:
            rating.score = score

        await self.db.flush()
        await self._refresh_note_rating(note.id)
        await self._refresh_user_rating(note.owner_id)
        await self.db.commit()
        updated_note = await self.note_service.get_note_by_id(note.id)
        my_score = await self.get_my_score(user.id, note.id)
        return updated_note, my_score

    async def get_rating(self, user: User, note_id: UUID) -> tuple[Note, int | None]:
        note = await self.note_service.get_note_for_viewer(user, note_id)
        my_score = await self.get_my_score(user.id, note.id)
        return note, my_score

    async def get_comment(self, comment_id: UUID) -> NoteComment:
        comment = await self.db.scalar(
            select(NoteComment)
            .options(joinedload(NoteComment.user))
            .where(NoteComment.id == comment_id)
        )
        if comment is None:
            raise LookupError("Comment not found")
        return comment

    async def get_my_score(self, user_id: UUID, note_id: UUID) -> int | None:
        rating = await self.db.scalar(
            select(NoteRating).where(
                NoteRating.note_id == note_id,
                NoteRating.user_id == user_id,
            )
        )
        return rating.score if rating is not None else None

    async def _refresh_note_rating(self, note_id: UUID) -> None:
        row = await self.db.execute(
            select(
                func.coalesce(func.avg(NoteRating.score), 0.0),
                func.count(NoteRating.id),
            ).where(NoteRating.note_id == note_id)
        )
        avg_value, count_value = row.one()
        note = await self.db.scalar(select(Note).where(Note.id == note_id))
        if note is None:
            return
        note.rating_avg = float(avg_value or 0.0)
        note.rating_count = int(count_value or 0)

    async def _refresh_user_rating(self, user_id: UUID) -> None:
        row = await self.db.execute(
            select(
                func.coalesce(func.avg(NoteRating.score), 0.0),
                func.count(NoteRating.id),
            )
            .join(Note, Note.id == NoteRating.note_id)
            .where(
                Note.owner_id == user_id,
                Note.is_published.is_(True),
            )
        )
        avg_value, count_value = row.one()
        user = await self.db.scalar(select(User).where(User.id == user_id))
        if user is None:
            return
        user.rating_avg = float(avg_value or 0.0)
        user.rating_count = int(count_value or 0)
