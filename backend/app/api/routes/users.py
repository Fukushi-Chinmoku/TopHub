from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, get_note_service, get_user_service
from app.api.routes.notes import _to_note_out
from app.models.user import User
from app.schemas.note import NoteOut
from app.schemas.user import UserSearchOut
from app.services.note_service import NoteService
from app.services.user_service import UserService


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/search", response_model=list[UserSearchOut])
async def search_users(
    q: str = Query(min_length=1, max_length=32),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> list[UserSearchOut]:
    users = await user_service.search_by_login_prefix(q, current_user.id)
    return [UserSearchOut(id=user.id, login=user.login, display_name=user.display_name) for user in users]


@router.get("/{login}/notes", response_model=list[NoteOut])
async def get_user_notes(
    login: str,
    subject: str | None = Query(default=None, max_length=128),
    sort: str = Query(default="-created_at", pattern="^(-created_at|created_at)$"),
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> list[NoteOut]:
    try:
        notes = await note_service.list_visible_notes_by_login(current_user, login, subject, sort)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [_to_note_out(note) for note in notes]
