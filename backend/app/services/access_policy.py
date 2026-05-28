from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import GroupMembership
from app.models.note import Note


class AccessPolicy:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def can_view(self, user_id, note: Note) -> bool:
        if note.owner_id == user_id:
            return True
        if not note.is_published:
            return False
        if note.visibility == "public":
            return True
        if note.visibility == "group" and note.group_id is not None:
            membership = await self.db.scalar(
                select(GroupMembership).where(
                    GroupMembership.group_id == note.group_id,
                    GroupMembership.user_id == user_id,
                    GroupMembership.status == "active",
                )
            )
            return membership is not None
        return False

    async def can_edit(self, user_id, note: Note) -> bool:
        if note.owner_id == user_id:
            return True
        if note.visibility == "private":
            return False
        if note.visibility == "public":
            return True
        if note.visibility == "group" and note.group_id is not None:
            membership = await self.db.scalar(
                select(GroupMembership).where(
                    GroupMembership.group_id == note.group_id,
                    GroupMembership.user_id == user_id,
                    GroupMembership.status == "active",
                )
            )
            return membership is not None
        return False

    async def can_comment(self, user_id, note: Note) -> bool:
        return await self.can_view(user_id, note) and note.is_published

    async def can_rate(self, user_id, note: Note) -> bool:
        return await self.can_view(user_id, note) and note.is_published and note.owner_id != user_id
