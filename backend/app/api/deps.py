from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.engagement_service import EngagementService
from app.services.friend_service import FriendService
from app.services.group_service import GroupService
from app.services.note_service import NoteService
from app.services.user_service import UserService


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_group_service(db: AsyncSession = Depends(get_db)) -> GroupService:
    return GroupService(db)


def get_friend_service(db: AsyncSession = Depends(get_db)) -> FriendService:
    return FriendService(db)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


def get_note_service(db: AsyncSession = Depends(get_db)) -> NoteService:
    return NoteService(db)


def get_engagement_service(db: AsyncSession = Depends(get_db)) -> EngagementService:
    return EngagementService(db)


async def get_current_user(
    session_id: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    user = await auth_service.get_current_user(session_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user
