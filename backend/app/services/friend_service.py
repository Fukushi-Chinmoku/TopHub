from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.friendship import Friendship
from app.models.user import User


class FriendService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def send_request(self, user: User, target_login: str) -> Friendship:
        target = await self.db.scalar(select(User).where(User.login == target_login.strip()))
        if target is None:
            raise ValueError("User not found")
        if target.id == user.id:
            raise ValueError("Cannot send friend request to yourself")

        friendship = await self.db.scalar(
            select(Friendship).where(
                or_(
                    (Friendship.requester_id == user.id) & (Friendship.addressee_id == target.id),
                    (Friendship.requester_id == target.id) & (Friendship.addressee_id == user.id),
                )
            )
        )

        if friendship is None:
            friendship = Friendship(
                requester_id=user.id,
                addressee_id=target.id,
                status="pending",
            )
            self.db.add(friendship)
        elif friendship.status == "accepted":
            raise ValueError("Already friends")
        elif friendship.requester_id == user.id and friendship.status == "pending":
            raise ValueError("Request already sent")
        elif friendship.addressee_id == user.id and friendship.status == "pending":
            raise ValueError("User already sent a request to you")
        else:
            friendship.requester_id = user.id
            friendship.addressee_id = target.id
            friendship.status = "pending"

        await self.db.commit()
        await self.db.refresh(friendship)
        return friendship

    async def incoming_requests(self, user: User) -> list[tuple[Friendship, User]]:
        requester = aliased(User)
        query = (
            select(Friendship, requester)
            .join(requester, requester.id == Friendship.requester_id)
            .where(
                Friendship.addressee_id == user.id,
                Friendship.status == "pending",
            )
            .order_by(Friendship.created_at.desc())
        )
        rows = await self.db.execute(query)
        return list(rows.all())

    async def respond_request(self, user: User, request_id: UUID, action: str) -> Friendship:
        friendship = await self.db.scalar(
            select(Friendship).where(
                Friendship.id == request_id,
                Friendship.addressee_id == user.id,
                Friendship.status == "pending",
            )
        )
        if friendship is None:
            raise LookupError("Friend request not found")

        friendship.status = "accepted" if action == "accept" else "rejected"
        await self.db.commit()
        await self.db.refresh(friendship)
        return friendship

    async def list_friends(self, user: User) -> list[tuple[User, Friendship]]:
        query = (
            select(Friendship)
            .where(
                Friendship.status == "accepted",
                or_(Friendship.requester_id == user.id, Friendship.addressee_id == user.id),
            )
            .order_by(Friendship.updated_at.desc())
        )
        friendships = list((await self.db.scalars(query)).all())
        friend_ids = [
            friendship.addressee_id if friendship.requester_id == user.id else friendship.requester_id
            for friendship in friendships
        ]
        if not friend_ids:
            return []

        users = list((await self.db.scalars(select(User).where(User.id.in_(friend_ids)))).all())
        users_by_id = {item.id: item for item in users}

        result: list[tuple[User, Friendship]] = []
        for friendship in friendships:
            friend_id = friendship.addressee_id if friendship.requester_id == user.id else friendship.requester_id
            friend = users_by_id.get(friend_id)
            if friend is not None:
                result.append((friend, friendship))
        return result

    async def remove_friend(self, user: User, friend_user_id: UUID) -> None:
        if friend_user_id == user.id:
            raise ValueError("Cannot remove yourself")

        friendship = await self.db.scalar(
            select(Friendship).where(
                Friendship.status == "accepted",
                or_(
                    (Friendship.requester_id == user.id) & (Friendship.addressee_id == friend_user_id),
                    (Friendship.requester_id == friend_user_id) & (Friendship.addressee_id == user.id),
                ),
            )
        )
        if friendship is None:
            raise LookupError("Friendship not found")

        await self.db.delete(friendship)
        await self.db.commit()
