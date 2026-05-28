import base64
import binascii
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings
from app.db.session import SessionLocal
from app.services.auth_service import AuthService
from app.services.note_service import NoteService
from app.ws.collaboration import hub


router = APIRouter()


@router.websocket("/ws/notes/{note_id}")
async def note_collaboration(websocket: WebSocket, note_id: UUID) -> None:
    awareness_client_id: int | None = None
    session_cookie = websocket.cookies.get(settings.session_cookie_name)
    if not session_cookie:
        await websocket.close(code=1008)
        return

    async with SessionLocal() as db:
        auth_service = AuthService(db)
        note_service = NoteService(db)
        user = await auth_service.get_current_user(session_cookie)
        if user is None:
            await websocket.close(code=1008)
            return
        try:
            note = await note_service.get_note_by_id(note_id)
        except LookupError:
            await websocket.close(code=1008)
            return
        can_edit = await note_service.can_edit_note(user.id, note)
        if not can_edit:
            await websocket.close(code=1008)
            return

    await hub.connect(
        note_id,
        websocket,
        {
            "id": str(user.id),
            "login": user.login,
            "display_name": user.display_name,
        },
    )
    await hub.send_presence(note_id)

    try:
        async with SessionLocal() as db:
            note_service = NoteService(db)
            note = await note_service.get_note_by_id(note_id)
            await websocket.send_json(
                {
                    "type": "content_sync",
                    "note_id": str(note_id),
                    "content_html": note.content_html or "",
                    "content_yjs_base64": base64.b64encode(note.content_yjs).decode("ascii")
                    if note.content_yjs
                    else None,
                }
            )

        while True:
            payload = await websocket.receive_json()
            payload_type = payload.get("type")
            if payload_type not in {"content_update", "yjs_update", "awareness_update"}:
                continue

            if payload_type == "awareness_update":
                awareness_client_id_value = payload.get("awareness_client_id")
                if not isinstance(awareness_client_id_value, int) or awareness_client_id_value < 0:
                    continue
                awareness_update_base64 = payload.get("awareness_update_base64")
                if not isinstance(awareness_update_base64, str) or len(awareness_update_base64) > 200_000:
                    continue
                try:
                    base64.b64decode(awareness_update_base64.encode("ascii"), validate=True)
                except (ValueError, binascii.Error):
                    continue
                awareness_client_id = awareness_client_id_value
                message = {
                    "type": "awareness_update",
                    "note_id": str(note_id),
                    "awareness_client_id": awareness_client_id_value,
                    "awareness_update_base64": awareness_update_base64,
                }
                await hub.broadcast(note_id, message, exclude=websocket)
                await hub.publish_update(note_id, message)
                continue

            if payload_type == "yjs_update":
                yjs_update_base64 = payload.get("yjs_update_base64")
                if not isinstance(yjs_update_base64, str) or len(yjs_update_base64) > 3_000_000:
                    continue
                try:
                    base64.b64decode(yjs_update_base64.encode("ascii"), validate=True)
                except (ValueError, binascii.Error):
                    continue
                content_yjs_base64 = payload.get("content_yjs_base64")
                content_yjs = None
                if content_yjs_base64 is not None:
                    if not isinstance(content_yjs_base64, str) or len(content_yjs_base64) > 3_000_000:
                        continue
                    try:
                        content_yjs = base64.b64decode(content_yjs_base64.encode("ascii"), validate=True)
                    except (ValueError, binascii.Error):
                        continue
                content_html = payload.get("content_html")
                if content_html is not None and not isinstance(content_html, str):
                    continue
                if isinstance(content_html, str) and len(content_html) > 500_000:
                    continue
                async with SessionLocal() as db:
                    note_service = NoteService(db)
                    if content_yjs is None:
                        note = await note_service.get_note_by_id(note_id)
                        content_yjs = note.content_yjs
                    if content_yjs is not None:
                        updated_note = await note_service.update_note_yjs_content(
                            note_id,
                            content_yjs,
                            content_html,
                        )
                    else:
                        updated_note = await note_service.update_note_content(
                            note_id,
                            content_html or "",
                        )

                message = {
                    "type": "yjs_update",
                    "note_id": str(note_id),
                    "yjs_update_base64": yjs_update_base64,
                    "updated_at": updated_note.updated_at.isoformat(),
                }
                await hub.broadcast(note_id, message, exclude=websocket)
                await hub.publish_update(note_id, message)
                await websocket.send_json(
                    {
                        "type": "content_saved",
                        "note_id": str(note_id),
                        "updated_at": updated_note.updated_at.isoformat(),
                    }
                )
                continue

            content_html = payload.get("content_html", "")
            if not isinstance(content_html, str):
                continue
            if len(content_html) > 500_000:
                continue

            async with SessionLocal() as db:
                note_service = NoteService(db)
                updated_note = await note_service.update_note_content(note_id, content_html)

            await hub.broadcast(
                note_id,
                {
                    "type": "content_update",
                    "note_id": str(note_id),
                    "content_html": content_html,
                    "updated_at": updated_note.updated_at.isoformat(),
                },
                exclude=websocket,
            )
            await hub.publish_update(
                note_id,
                {
                    "type": "content_update",
                    "note_id": str(note_id),
                    "content_html": content_html,
                    "updated_at": updated_note.updated_at.isoformat(),
                },
            )
            await websocket.send_json(
                {
                    "type": "content_saved",
                    "note_id": str(note_id),
                    "updated_at": updated_note.updated_at.isoformat(),
                }
            )
    except WebSocketDisconnect:
        pass
    finally:
        hub.disconnect(note_id, websocket)
        if awareness_client_id is not None:
            clear_message = {
                "type": "awareness_remove",
                "note_id": str(note_id),
                "awareness_client_id": awareness_client_id,
            }
            await hub.broadcast(note_id, clear_message)
            await hub.publish_update(note_id, clear_message)
        await hub.send_presence(note_id)
