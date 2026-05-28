from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.group import Group, GroupMembership
from app.models.note import Note
from app.models.user import User


class GroupService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_group(self, user: User, name: str) -> Group:
        normalized_name = self._normalize_name(name)
        existing = await self.db.scalar(select(Group).where(func.lower(Group.name) == normalized_name.lower()))
        if existing is not None:
            raise ValueError("Group name already exists")

        group = Group(name=normalized_name, owner_id=user.id)
        self.db.add(group)
        await self.db.flush()

        membership = GroupMembership(
            group_id=group.id,
            user_id=user.id,
            role="owner",
            status="active",
        )
        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def request_join(self, user: User, name: str) -> GroupMembership:
        normalized_name = self._normalize_name(name)
        group = await self.db.scalar(select(Group).where(func.lower(Group.name) == normalized_name.lower()))
        if group is None:
            raise ValueError("Group not found")

        membership = await self.db.scalar(
            select(GroupMembership).where(
                GroupMembership.group_id == group.id,
                GroupMembership.user_id == user.id,
            )
        )
        if membership is None:
            membership = GroupMembership(
                group_id=group.id,
                user_id=user.id,
                role="member",
                status="pending",
            )
            self.db.add(membership)
        elif membership.status == "active":
            raise ValueError("You are already a member of this group")
        else:
            membership.status = "pending"

        await self.db.commit()
        await self.db.refresh(membership)
        return membership

    async def list_my_groups(self, user: User) -> list[Group]:
        query = (
            select(Group)
            .join(GroupMembership, GroupMembership.group_id == Group.id)
            .where(
                GroupMembership.user_id == user.id,
                GroupMembership.status == "active",
            )
            .order_by(Group.created_at.desc())
        )
        result = await self.db.scalars(query)
        return list(result.all())

    async def get_group_for_member(self, user: User, group_id: UUID) -> Group:
        group = await self.db.scalar(
            select(Group)
            .options(joinedload(Group.memberships))
            .where(Group.id == group_id)
        )
        if group is None:
            raise LookupError("Group not found")

        membership = await self.db.scalar(
            select(GroupMembership).where(
                GroupMembership.group_id == group.id,
                GroupMembership.user_id == user.id,
                GroupMembership.status == "active",
            )
        )
        if membership is None:
            raise PermissionError("Access denied")
        return group

    async def list_members(self, user: User, group_id: UUID) -> list[GroupMembership]:
        await self.get_group_for_member(user, group_id)
        query = (
            select(GroupMembership)
            .options(joinedload(GroupMembership.user))
            .where(
                GroupMembership.group_id == group_id,
                GroupMembership.status == "active",
            )
            .order_by(GroupMembership.created_at.asc())
        )
        result = await self.db.scalars(query)
        return list(result.all())

    async def list_pending_requests(self, user: User, group_id: UUID) -> list[GroupMembership]:
        group = await self.db.scalar(select(Group).where(Group.id == group_id))
        if group is None:
            raise LookupError("Group not found")
        if group.owner_id != user.id:
            raise PermissionError("Only group owner can view join requests")

        query = (
            select(GroupMembership)
            .options(joinedload(GroupMembership.user))
            .where(
                GroupMembership.group_id == group_id,
                GroupMembership.status == "pending",
            )
            .order_by(GroupMembership.created_at.asc())
        )
        result = await self.db.scalars(query)
        return list(result.all())

    async def handle_request(
        self,
        user: User,
        group_id: UUID,
        target_user_id: UUID,
        action: str,
    ) -> GroupMembership:
        group = await self.db.scalar(select(Group).where(Group.id == group_id))
        if group is None:
            raise LookupError("Group not found")
        if group.owner_id != user.id:
            raise PermissionError("Only group owner can manage requests")

        membership = await self.db.scalar(
            select(GroupMembership).where(
                GroupMembership.group_id == group_id,
                GroupMembership.user_id == target_user_id,
                GroupMembership.status == "pending",
            )
        )
        if membership is None:
            raise LookupError("Join request not found")

        membership.status = "active" if action == "accept" else "rejected"
        await self.db.commit()
        await self.db.refresh(membership)
        return membership

    async def delete_group(self, user: User, group_id: UUID) -> None:
        group = await self.db.scalar(select(Group).where(Group.id == group_id))
        if group is None:
            raise LookupError("Group not found")
        if group.owner_id != user.id:
            raise PermissionError("Only group owner can delete the group")

        notes = await self.db.scalars(select(Note).where(Note.group_id == group_id))
        for note in notes:
            note.visibility = "private"
            note.group_id = None

        await self.db.delete(group)
        await self.db.commit()

    async def leave_group(self, user: User, group_id: UUID) -> None:
        group = await self.db.scalar(select(Group).where(Group.id == group_id))
        if group is None:
            raise LookupError("Group not found")
        if group.owner_id == user.id:
            raise ValueError("Group owner cannot leave the group")

        membership = await self.db.scalar(
            select(GroupMembership).where(
                GroupMembership.group_id == group_id,
                GroupMembership.user_id == user.id,
                GroupMembership.status == "active",
            )
        )
        if membership is None:
            raise LookupError("You are not a member of this group")

        await self.db.delete(membership)
        await self.db.commit()

    @staticmethod
    def _normalize_name(name: str) -> str:
        normalized = name.strip()
        if len(normalized) < 3:
            raise ValueError("Group name is too short")
        return normalized
