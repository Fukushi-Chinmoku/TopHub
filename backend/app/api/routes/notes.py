from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, get_engagement_service, get_note_service
from app.models.note import Note
from app.models.note_revision import NoteRevision
from app.models.user import User
from app.schemas.engagement import CommentCreateRequest, CommentOut, RatingOut, RatingRequest
from app.schemas.note import NoteCreateRequest, NoteOut, NoteRevisionOut, NoteUpdateRequest
from app.services.engagement_service import EngagementService
from app.services.note_service import NoteService


router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreateRequest,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> NoteOut:
    try:
        note = await note_service.create_note(current_user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_note_out(note)


@router.get("", response_model=list[NoteOut])
async def list_my_notes(
    subject: str | None = Query(default=None, max_length=128),
    subject_id: UUID | None = Query(default=None),
    visibility: str | None = Query(default=None, pattern="^(private|public|group)$"),
    sort: str = Query(default="-created_at", pattern="^(-created_at|created_at)$"),
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> list[NoteOut]:
    notes = await note_service.list_my_notes(current_user, subject, subject_id, visibility, sort)
    return [_to_note_out(note) for note in notes]


@router.get("/public", response_model=list[NoteOut])
async def list_public_notes(
    subject: str | None = Query(default=None, max_length=128),
    subject_id: UUID | None = Query(default=None),
    sort: str = Query(default="-created_at", pattern="^(-created_at|created_at)$"),
    q: str | None = Query(default=None, max_length=128),
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> list[NoteOut]:
    _ = current_user
    notes = await note_service.list_public_notes(subject, subject_id, sort, q)
    return [_to_note_out(note, include_owner=True) for note in notes]


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> NoteOut:
    try:
        note = await note_service.get_note_for_viewer(current_user, note_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return _to_note_out(note)


@router.patch("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: UUID,
    payload: NoteUpdateRequest,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> NoteOut:
    try:
        note = await note_service.update_note(current_user, note_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_note_out(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> None:
    try:
        await note_service.delete_note(current_user, note_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{note_id}/publish", response_model=NoteOut)
async def publish_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> NoteOut:
    try:
        note = await note_service.publish_note(current_user, note_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_note_out(note)


@router.get("/{note_id}/comments", response_model=list[CommentOut])
async def list_comments(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    engagement_service: EngagementService = Depends(get_engagement_service),
) -> list[CommentOut]:
    try:
        comments = await engagement_service.list_comments(current_user, note_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return [_to_comment_out(item) for item in comments]


@router.post("/{note_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_comment(
    note_id: UUID,
    payload: CommentCreateRequest,
    current_user: User = Depends(get_current_user),
    engagement_service: EngagementService = Depends(get_engagement_service),
) -> CommentOut:
    try:
        comment = await engagement_service.add_comment(current_user, note_id, payload.content)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_comment_out(comment)


@router.get("/{note_id}/rating", response_model=RatingOut)
async def get_rating(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    engagement_service: EngagementService = Depends(get_engagement_service),
) -> RatingOut:
    try:
        note, my_score = await engagement_service.get_rating(current_user, note_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return RatingOut(
        note_id=note.id,
        rating_avg=note.rating_avg,
        rating_count=note.rating_count,
        my_score=my_score,
    )


@router.put("/{note_id}/rating", response_model=RatingOut)
async def put_rating(
    note_id: UUID,
    payload: RatingRequest,
    current_user: User = Depends(get_current_user),
    engagement_service: EngagementService = Depends(get_engagement_service),
) -> RatingOut:
    try:
        note, my_score = await engagement_service.rate_note(current_user, note_id, payload.score)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RatingOut(
        note_id=note.id,
        rating_avg=note.rating_avg,
        rating_count=note.rating_count,
        my_score=my_score,
    )


@router.get("/{note_id}/revisions", response_model=list[NoteRevisionOut])
async def list_revisions(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> list[NoteRevisionOut]:
    try:
        revisions = await note_service.list_revisions(current_user, note_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return [_to_revision_out(item) for item in revisions]


@router.post("/{note_id}/revisions", response_model=NoteRevisionOut, status_code=status.HTTP_201_CREATED)
async def create_revision(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> NoteRevisionOut:
    try:
        revision = await note_service.create_revision(current_user, note_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return _to_revision_out(revision)


@router.post("/{note_id}/revisions/{revision_id}/restore", response_model=NoteOut)
async def restore_revision(
    note_id: UUID,
    revision_id: UUID,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> NoteOut:
    try:
        note = await note_service.restore_revision(current_user, note_id, revision_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return _to_note_out(note)


@router.delete("/{note_id}/revisions/{revision_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_revision(
    note_id: UUID,
    revision_id: UUID,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
) -> None:
    try:
        await note_service.delete_revision(current_user, note_id, revision_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


def _to_note_out(note: Note, *, include_owner: bool = False) -> NoteOut:
    owner_login = None
    owner_display_name = None
    if include_owner and note.owner is not None:
        owner_login = note.owner.login
        owner_display_name = note.owner.display_name
    return NoteOut(
        id=note.id,
        owner_id=note.owner_id,
        owner_login=owner_login,
        owner_display_name=owner_display_name,
        title=note.title,
        description=note.description,
        outline=note.outline,
        subject_id=note.subject_id,
        subject_name=note.subject.name if note.subject else None,
        subject_custom=note.subject_custom,
        visibility=note.visibility,
        group_id=note.group_id,
        is_published=note.is_published,
        content_html=note.content_html,
        tags=[item.tag for item in note.tags],
        rating_avg=note.rating_avg,
        rating_count=note.rating_count,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def _to_comment_out(comment) -> CommentOut:
    return CommentOut(
        id=comment.id,
        note_id=comment.note_id,
        user_id=comment.user_id,
        login=comment.user.login,
        display_name=comment.user.display_name,
        content=comment.content,
        created_at=comment.created_at,
    )


def _to_revision_out(revision: NoteRevision) -> NoteRevisionOut:
    return NoteRevisionOut(
        id=revision.id,
        note_id=revision.note_id,
        author_id=revision.author_id,
        content_html=revision.content_html,
        created_at=revision.created_at,
    )
