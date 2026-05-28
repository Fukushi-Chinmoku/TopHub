from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_note_service
from app.api.routes.notes import _to_note_out
from app.models.user import User
from app.schemas.note import CabinetOut
from app.services.note_service import NoteService


router = APIRouter(prefix="/cabinet", tags=["cabinet"])


@router.get("", response_model=CabinetOut)
async def get_cabinet(
    subject: str | None = Query(default=None, max_length=128),
    subject_id: UUID | None = Query(default=None),
    visibility: str | None = Query(default=None, pattern="^(private|public|group)$"),
    sort: str = Query(default="-created_at", pattern="^(-created_at|created_at)$"),
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> CabinetOut:
    notes = await note_service.list_my_notes(current_user, subject, subject_id, visibility, sort)
    return CabinetOut(
        user_id=current_user.id,
        rating_avg=current_user.rating_avg,
        rating_count=current_user.rating_count,
        notes=[_to_note_out(note) for note in notes],
    )
