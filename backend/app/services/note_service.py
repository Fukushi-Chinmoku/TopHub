from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.group import GroupMembership
from app.models.note import Note, NoteTag
from app.models.note_revision import NoteRevision
from app.models.subject import Subject
from app.models.user import User
from app.schemas.note import NoteCreateRequest, NoteUpdateRequest
from app.services.access_policy import AccessPolicy


class NoteService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.policy = AccessPolicy(db)

    async def list_subjects(self) -> list[Subject]:
        result = await self.db.scalars(select(Subject).order_by(Subject.name.asc()))
        return list(result.all())

    async def create_note(self, user: User, payload: NoteCreateRequest) -> Note:
        await self._validate_subject(payload.subject_id, payload.subject_custom)
        await self._validate_visibility(user.id, payload.visibility, payload.group_id)

        note = Note(
            owner_id=user.id,
            title=payload.title.strip(),
            description=payload.description.strip(),
            outline=[item.model_dump() for item in payload.outline],
            subject_id=payload.subject_id,
            subject_custom=(payload.subject_custom or "").strip() or None,
            visibility=payload.visibility,
            group_id=payload.group_id if payload.visibility == "group" else None,
            is_published=False,
        )
        self.db.add(note)
        await self.db.flush()
        await self._replace_tags(note.id, payload.tags)
        await self.db.commit()
        return await self.get_note_by_id(note.id)

    async def update_note(self, user: User, note_id: UUID, payload: NoteUpdateRequest) -> Note:
        note = await self._get_owned_note(user.id, note_id)
        if note is None:
            raise LookupError("Note not found")

        fields_set = payload.model_fields_set
        next_subject_id = payload.subject_id if "subject_id" in fields_set else note.subject_id
        next_subject_custom = (
            payload.subject_custom if "subject_custom" in fields_set else note.subject_custom
        )
        next_visibility = payload.visibility if payload.visibility is not None else note.visibility
        next_group_id = payload.group_id if payload.group_id is not None else note.group_id

        await self._validate_subject(next_subject_id, next_subject_custom)
        await self._validate_visibility(user.id, next_visibility, next_group_id)

        if payload.title is not None:
            note.title = payload.title.strip()
        if payload.description is not None:
            note.description = payload.description.strip()
        if payload.outline is not None:
            note.outline = [item.model_dump() for item in payload.outline]
        if "subject_id" in fields_set:
            note.subject_id = payload.subject_id
        if "subject_custom" in fields_set:
            note.subject_custom = (payload.subject_custom or "").strip() or None
        if payload.visibility is not None:
            note.visibility = payload.visibility
            if payload.visibility != "group":
                note.group_id = None
        if payload.group_id is not None and (payload.visibility == "group" or note.visibility == "group"):
            note.group_id = payload.group_id
        if payload.tags is not None:
            await self._replace_tags(note.id, payload.tags)
        if payload.content_html is not None:
            note.content_html = payload.content_html

        await self.db.commit()
        return await self.get_note_by_id(note.id)

    async def publish_note(self, user: User, note_id: UUID) -> Note:
        note = await self._get_owned_note(user.id, note_id)
        if note is None:
            raise LookupError("Note not found")
        if note.visibility == "private":
            raise ValueError("Private note cannot be published")
        note.is_published = True
        await self.db.commit()
        return await self.get_note_by_id(note.id)

    async def get_note_for_owner(self, user: User, note_id: UUID) -> Note:
        note = await self._get_owned_note(user.id, note_id)
        if note is None:
            raise LookupError("Note not found")
        return await self.get_note_by_id(note.id)

    async def get_note_for_viewer(self, user: User, note_id: UUID) -> Note:
        note = await self.get_note_by_id(note_id)
        if await self.can_view_note(user.id, note):
            return note
        raise PermissionError("Access denied")

    async def update_note_content(self, note_id: UUID, content_html: str) -> Note:
        note = await self.db.scalar(select(Note).where(Note.id == note_id))
        if note is None:
            raise LookupError("Note not found")
        note.content_html = content_html
        note.content_yjs = None
        await self.db.commit()
        return note

    async def update_note_yjs_content(
        self,
        note_id: UUID,
        content_yjs: bytes,
        content_html: str | None,
    ) -> Note:
        note = await self.db.scalar(select(Note).where(Note.id == note_id))
        if note is None:
            raise LookupError("Note not found")
        note.content_yjs = content_yjs
        if content_html is not None:
            note.content_html = content_html
        await self.db.commit()
        return note

    async def update_note_content_with_revisions(
        self,
        note_id: UUID,
        content_html: str,
        author_id: UUID | None,
    ) -> Note:
        note = await self.db.scalar(select(Note).where(Note.id == note_id))
        if note is None:
            raise LookupError("Note not found")
        note.content_html = content_html
        note.content_yjs = None
        await self._maybe_create_periodic_revision(note, author_id)
        await self.db.commit()
        return note

    async def update_note_yjs_content_with_revisions(
        self,
        note_id: UUID,
        content_yjs: bytes,
        content_html: str | None,
        author_id: UUID | None,
    ) -> Note:
        note = await self.db.scalar(select(Note).where(Note.id == note_id))
        if note is None:
            raise LookupError("Note not found")
        note.content_yjs = content_yjs
        if content_html is not None:
            note.content_html = content_html
        await self._maybe_create_periodic_revision(note, author_id)
        await self.db.commit()
        return note

    async def delete_note(self, user: User, note_id: UUID) -> None:
        note = await self._get_owned_note(user.id, note_id)
        if note is None:
            raise LookupError("Note not found")
        await self.db.delete(note)
        await self.db.commit()

    async def list_public_notes(
        self,
        subject: str | None,
        subject_id: UUID | None,
        sort: str,
        q: str | None,
    ) -> list[Note]:
        query = (
            select(Note)
            .options(selectinload(Note.tags), joinedload(Note.subject), joinedload(Note.owner))
            .where(
                Note.is_published.is_(True),
                Note.visibility == "public",
            )
        )
        query = self._apply_subject_filter(query, subject, subject_id)
        if q:
            pattern = f"%{q.strip()}%"
            query = query.where(
                or_(
                    Note.title.ilike(pattern),
                    Note.description.ilike(pattern),
                )
            )
        query = query.order_by(Note.created_at.asc() if sort == "created_at" else desc(Note.created_at))
        result = await self.db.scalars(query)
        return list(result.unique().all())

    async def list_my_notes(
        self,
        user: User,
        subject: str | None,
        subject_id: UUID | None,
        visibility: str | None,
        sort: str,
    ) -> list[Note]:
        query = (
            select(Note)
            .options(selectinload(Note.tags), joinedload(Note.subject))
            .where(Note.owner_id == user.id)
        )
        query = self._apply_subject_filter(query, subject, subject_id)
        if visibility:
            query = query.where(Note.visibility == visibility)

        query = query.order_by(Note.created_at.asc() if sort == "created_at" else desc(Note.created_at))
        result = await self.db.scalars(query)
        return list(result.all())

    async def list_group_notes(
        self,
        user: User,
        group_id: UUID,
        author_id: UUID | None,
        subject: str | None,
        subject_id: UUID | None,
        sort: str,
    ) -> list[Note]:
        is_member = await self.db.scalar(
            select(GroupMembership).where(
                GroupMembership.group_id == group_id,
                GroupMembership.user_id == user.id,
                GroupMembership.status == "active",
            )
        )
        if is_member is None:
            raise PermissionError("Access denied")

        query = (
            select(Note)
            .options(selectinload(Note.tags), joinedload(Note.subject))
            .where(
                Note.group_id == group_id,
                Note.visibility == "group",
                Note.is_published.is_(True),
            )
        )
        if author_id is not None:
            query = query.where(Note.owner_id == author_id)
        query = self._apply_subject_filter(query, subject, subject_id)

        query = query.order_by(Note.created_at.asc() if sort == "created_at" else desc(Note.created_at))
        result = await self.db.scalars(query)
        return list(result.all())

    async def list_visible_notes_by_login(
        self,
        current_user: User,
        login: str,
        subject: str | None,
        sort: str,
    ) -> list[Note]:
        target_user = await self.db.scalar(select(User).where(User.login == login))
        if target_user is None:
            raise LookupError("User not found")

        membership_alias = GroupMembership
        query = (
            select(Note)
            .options(selectinload(Note.tags), joinedload(Note.subject))
            .outerjoin(
                membership_alias,
                and_(
                    membership_alias.group_id == Note.group_id,
                    membership_alias.user_id == current_user.id,
                    membership_alias.status == "active",
                ),
            )
            .where(
                Note.owner_id == target_user.id,
                Note.is_published.is_(True),
                or_(
                    Note.visibility == "public",
                    and_(Note.visibility == "group", membership_alias.id.is_not(None)),
                ),
            )
        )

        if subject:
            query = query.where(
                or_(
                    func.lower(Note.subject_custom) == subject.lower(),
                    Note.subject.has(func.lower(Subject.name) == subject.lower()),
                )
            )

        query = query.order_by(Note.created_at.asc() if sort == "created_at" else desc(Note.created_at))
        result = await self.db.scalars(query)
        return list(result.unique().all())

    async def get_note_by_id(self, note_id: UUID) -> Note:
        note = await self.db.scalar(
            select(Note)
            .options(selectinload(Note.tags), joinedload(Note.subject))
            .where(Note.id == note_id)
        )
        if note is None:
            raise LookupError("Note not found")
        return note

    async def list_revisions(self, user: User, note_id: UUID) -> list[NoteRevision]:
        note = await self.get_note_by_id(note_id)
        if not await self.policy.can_edit(user.id, note):
            raise PermissionError("Access denied")
        result = await self.db.scalars(
            select(NoteRevision)
            .where(NoteRevision.note_id == note_id)
            .order_by(NoteRevision.created_at.desc())
        )
        return list(result.all())

    async def create_revision(self, user: User, note_id: UUID) -> NoteRevision:
        note = await self.get_note_by_id(note_id)
        if not await self.policy.can_edit(user.id, note):
            raise PermissionError("Access denied")
        revision = NoteRevision(
            note_id=note.id,
            author_id=user.id,
            content_html=note.content_html or "",
        )
        self.db.add(revision)
        await self.db.flush()
        await self._trim_revisions(note.id)
        await self.db.commit()
        await self.db.refresh(revision)
        return revision

    async def restore_revision(self, user: User, note_id: UUID, revision_id: UUID) -> Note:
        note = await self.get_note_by_id(note_id)
        if not await self.policy.can_edit(user.id, note):
            raise PermissionError("Access denied")
        revision = await self.db.scalar(
            select(NoteRevision).where(
                NoteRevision.id == revision_id,
                NoteRevision.note_id == note_id,
            )
        )
        if revision is None:
            raise LookupError("Revision not found")
        note.content_html = revision.content_html
        note.content_yjs = None
        await self.db.commit()
        return await self.get_note_by_id(note.id)

    async def delete_revision(self, user: User, note_id: UUID, revision_id: UUID) -> None:
        note = await self.get_note_by_id(note_id)
        if not await self.policy.can_edit(user.id, note):
            raise PermissionError("Access denied")
        revision = await self.db.scalar(
            select(NoteRevision).where(
                NoteRevision.id == revision_id,
                NoteRevision.note_id == note_id,
            )
        )
        if revision is None:
            raise LookupError("Revision not found")
        await self.db.delete(revision)
        await self.db.commit()

    @staticmethod
    def _apply_subject_filter(query, subject: str | None, subject_id: UUID | None):
        if subject_id is not None:
            return query.where(Note.subject_id == subject_id)
        if subject:
            return query.where(
                or_(
                    func.lower(Note.subject_custom) == subject.lower(),
                    Note.subject.has(func.lower(Subject.name) == subject.lower()),
                )
            )
        return query

    async def _replace_tags(self, note_id: UUID, tags: list[str]) -> None:
        normalized_tags: list[str] = []
        for item in tags:
            tag = item.strip().lower()
            if tag and tag not in normalized_tags:
                normalized_tags.append(tag)

        await self.db.execute(delete(NoteTag).where(NoteTag.note_id == note_id))
        await self.db.flush()
        for tag in normalized_tags:
            self.db.add(NoteTag(note_id=note_id, tag=tag))

    async def _validate_subject(self, subject_id: UUID | None, subject_custom: str | None) -> None:
        if subject_id is None and not (subject_custom or "").strip():
            raise ValueError("Subject is required")
        if subject_id is not None:
            subject = await self.db.scalar(select(Subject).where(Subject.id == subject_id))
            if subject is None:
                raise ValueError("Subject not found")

    async def _validate_visibility(self, user_id: UUID, visibility: str, group_id: UUID | None) -> None:
        if visibility == "group":
            if group_id is None:
                raise ValueError("group_id is required for group visibility")
            membership = await self.db.scalar(
                select(GroupMembership).where(
                    GroupMembership.group_id == group_id,
                    GroupMembership.user_id == user_id,
                    GroupMembership.status == "active",
                )
            )
            if membership is None:
                raise ValueError("You are not a member of this group")
        elif group_id is not None:
            raise ValueError("group_id is allowed only for group visibility")

    async def can_view_note(self, user_id: UUID, note: Note) -> bool:
        return await self.policy.can_view(user_id, note)

    async def can_edit_note(self, user_id: UUID, note: Note) -> bool:
        return await self.policy.can_edit(user_id, note)

    async def _get_owned_note(self, user_id: UUID, note_id: UUID) -> Note | None:
        return await self.db.scalar(
            select(Note).where(
                Note.id == note_id,
                Note.owner_id == user_id,
            )
        )

    async def _maybe_create_periodic_revision(self, note: Note, author_id: UUID | None) -> None:
        last_revision_time = await self.db.scalar(
            select(func.max(NoteRevision.created_at)).where(NoteRevision.note_id == note.id)
        )
        if note.content_html is None:
            return
        now = datetime.now(timezone.utc)
        if last_revision_time is not None and (now - last_revision_time) < timedelta(seconds=60):
            return
        self.db.add(
            NoteRevision(
                note_id=note.id,
                author_id=author_id,
                content_html=note.content_html,
            )
        )
        await self.db.flush()
        await self._trim_revisions(note.id)

    async def _trim_revisions(self, note_id: UUID, max_count: int = 20) -> None:
        revisions = list(
            (
                await self.db.scalars(
                    select(NoteRevision)
                    .where(NoteRevision.note_id == note_id)
                    .order_by(NoteRevision.created_at.desc())
                )
            ).all()
        )
        for extra in revisions[max_count:]:
            await self.db.delete(extra)
