from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_note_service
from app.models.user import User
from app.schemas.note import SubjectOut
from app.services.note_service import NoteService


router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=list[SubjectOut])
async def list_subjects(
    _: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> list[SubjectOut]:
    subjects = await note_service.list_subjects()
    return [SubjectOut(id=item.id, name=item.name) for item in subjects]
