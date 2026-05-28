import asyncio
import json
from collections import defaultdict
from uuid import UUID, uuid4

from fastapi import WebSocket
from redis.asyncio import Redis

from app.config import settings


class CollaborationHub:
    def __init__(self) -> None:
        self._rooms: dict[UUID, set[WebSocket]] = defaultdict(set)
        self._room_users: dict[UUID, dict[WebSocket, dict]] = defaultdict(dict)
        self._listeners: dict[UUID, asyncio.Task] = {}
        self._instance_id = str(uuid4())
        self._redis: Redis = Redis.from_url(settings.redis_url, decode_responses=True)

    async def connect(self, note_id: UUID, websocket: WebSocket, user: dict) -> None:
        await websocket.accept()
        self._rooms[note_id].add(websocket)
        self._room_users[note_id][websocket] = user
        await self._ensure_listener(note_id)

    def disconnect(self, note_id: UUID, websocket: WebSocket) -> None:
        room = self._rooms.get(note_id)
        if not room:
            return
        room.discard(websocket)
        room_users = self._room_users.get(note_id)
        if room_users is not None:
            room_users.pop(websocket, None)
            if not room_users:
                self._room_users.pop(note_id, None)
        if not room:
            self._rooms.pop(note_id, None)
            self._stop_listener(note_id)

    async def broadcast(self, note_id: UUID, message: dict, exclude: WebSocket | None = None) -> None:
        room = self._rooms.get(note_id, set())
        for client in list(room):
            if exclude is not None and client is exclude:
                continue
            try:
                await client.send_json(message)
            except Exception:
                self.disconnect(note_id, client)

    async def send_presence(self, note_id: UUID) -> None:
        users = list(self._room_users.get(note_id, {}).values())
        await self.broadcast(
            note_id,
            {
                "type": "presence",
                "note_id": str(note_id),
                "users": users,
            },
        )

    async def publish_update(self, note_id: UUID, message: dict) -> None:
        envelope = {"origin": self._instance_id, "payload": message}
        await self._redis.publish(self._channel(note_id), json.dumps(envelope))

    async def _ensure_listener(self, note_id: UUID) -> None:
        if note_id in self._listeners:
            return
        self._listeners[note_id] = asyncio.create_task(self._listen(note_id))

    def _stop_listener(self, note_id: UUID) -> None:
        task = self._listeners.pop(note_id, None)
        if task is not None:
            task.cancel()

    async def _listen(self, note_id: UUID) -> None:
        pubsub = self._redis.pubsub()
        channel = self._channel(note_id)
        await pubsub.subscribe(channel)
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is None:
                    await asyncio.sleep(0.05)
                    continue
                raw_data = message.get("data")
                if not isinstance(raw_data, str):
                    continue
                try:
                    envelope = json.loads(raw_data)
                except json.JSONDecodeError:
                    continue
                if envelope.get("origin") == self._instance_id:
                    continue
                payload = envelope.get("payload")
                if isinstance(payload, dict):
                    await self.broadcast(note_id, payload)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    @staticmethod
    def _channel(note_id: UUID) -> str:
        return f"notes:{note_id}:updates"


hub = CollaborationHub()
