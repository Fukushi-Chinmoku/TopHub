from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, get_group_service, get_note_service
from app.models.group import GroupMembership
from app.models.user import User
from app.schemas.note import NoteOut
from app.schemas.group import (
    GroupCreateRequest,
    GroupJoinRequest,
    GroupJoinRequestOut,
    GroupMemberOut,
    GroupOut,
    GroupRequestAction,
)
from app.services.group_service import GroupService
from app.services.note_service import NoteService
from app.api.routes.notes import _to_note_out


router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: GroupCreateRequest,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service),
) -> GroupOut:
    try:
        group = await group_service.create_group(current_user, payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return GroupOut.model_validate(group)


@router.get("/mine", response_model=list[GroupOut])
async def list_my_groups(
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service),
) -> list[GroupOut]:
    groups = await group_service.list_my_groups(current_user)
    return [GroupOut.model_validate(item) for item in groups]


@router.post("/join-request", response_model=dict[str, str], status_code=status.HTTP_201_CREATED)
async def join_request(
    payload: GroupJoinRequest,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service),
) -> dict[str, str]:
    try:
        await group_service.request_join(current_user, payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"status": "pending"}


@router.get("/{group_id}", response_model=GroupOut)
async def get_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service),
) -> GroupOut:
    try:
        group = await group_service.get_group_for_member(current_user, group_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return GroupOut.model_validate(group)


@router.get("/{group_id}/members", response_model=list[GroupMemberOut])
async def list_members(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service),
) -> list[GroupMemberOut]:
    try:
        memberships = await group_service.list_members(current_user, group_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return [_membership_to_out(item) for item in memberships]


@router.get("/{group_id}/requests/incoming", response_model=list[GroupJoinRequestOut])
async def incoming_join_requests(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service),
) -> list[GroupJoinRequestOut]:
    try:
        memberships = await group_service.list_pending_requests(current_user, group_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return [_join_request_to_out(item) for item in memberships]


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service),
) -> None:
    try:
        await group_service.delete_group(current_user, group_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{group_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service),
) -> None:
    try:
        await group_service.leave_group(current_user, group_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/{group_id}/requests/{user_id}", response_model=dict[str, str])
async def handle_request(
    group_id: UUID,
    user_id: UUID,
    payload: GroupRequestAction,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service),
) -> dict[str, str]:
    try:
        membership = await group_service.handle_request(current_user, group_id, user_id, payload.action)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return {"status": membership.status}


@router.get("/{group_id}/notes", response_model=list[NoteOut])
async def list_group_notes(
    group_id: UUID,
    author: UUID | None = Query(default=None),
    subject: str | None = Query(default=None, max_length=128),
    subject_id: UUID | None = Query(default=None),
    sort: str = Query(default="-created_at", pattern="^(-created_at|created_at)$"),
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> list[NoteOut]:
    try:
        notes = await note_service.list_group_notes(
            current_user, group_id, author, subject, subject_id, sort
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return [_to_note_out(note) for note in notes]


def _membership_to_out(membership: GroupMembership) -> GroupMemberOut:
    return GroupMemberOut(
        user_id=membership.user_id,
        login=membership.user.login,
        display_name=membership.user.display_name,
        role=membership.role,
        status=membership.status,
        created_at=membership.created_at,
    )


def _join_request_to_out(membership: GroupMembership) -> GroupJoinRequestOut:
    return GroupJoinRequestOut(
        user_id=membership.user_id,
        login=membership.user.login,
        display_name=membership.user.display_name,
        created_at=membership.created_at,
    )
