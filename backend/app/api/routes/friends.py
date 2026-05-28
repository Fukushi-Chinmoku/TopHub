from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_friend_service
from app.models.user import User
from app.schemas.friend import (
    FriendOut,
    FriendRequestAction,
    FriendRequestCreate,
    FriendRequestOut,
)
from app.services.friend_service import FriendService


router = APIRouter(prefix="/friends", tags=["friends"])


@router.post("/request", response_model=dict[str, str], status_code=status.HTTP_201_CREATED)
async def create_request(
    payload: FriendRequestCreate,
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
) -> dict[str, str]:
    try:
        await friend_service.send_request(current_user, payload.login)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"status": "pending"}


@router.get("", response_model=list[FriendOut])
async def list_friends(
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
) -> list[FriendOut]:
    rows = await friend_service.list_friends(current_user)
    return [
        FriendOut(
            user_id=friend.id,
            login=friend.login,
            display_name=friend.display_name,
            since=friendship.updated_at,
        )
        for friend, friendship in rows
    ]


@router.get("/requests/incoming", response_model=list[FriendRequestOut])
async def incoming_requests(
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
) -> list[FriendRequestOut]:
    rows = await friend_service.incoming_requests(current_user)
    return [
        FriendRequestOut(
            id=friendship.id,
            requester_id=requester.id,
            requester_login=requester.login,
            requester_display_name=requester.display_name,
            status=friendship.status,
            created_at=friendship.created_at,
        )
        for friendship, requester in rows
    ]


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
) -> None:
    try:
        await friend_service.remove_friend(current_user, user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/requests/{request_id}", response_model=dict[str, str])
async def respond_request(
    request_id: UUID,
    payload: FriendRequestAction,
    current_user: User = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
) -> dict[str, str]:
    try:
        friendship = await friend_service.respond_request(current_user, request_id, payload.action)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"status": friendship.status}
