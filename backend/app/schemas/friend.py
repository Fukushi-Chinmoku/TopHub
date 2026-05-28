from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FriendRequestCreate(BaseModel):
    login: str = Field(min_length=3, max_length=32)


class FriendRequestAction(BaseModel):
    action: str = Field(pattern="^(accept|reject)$")


class FriendRequestOut(BaseModel):
    id: UUID
    requester_id: UUID
    requester_login: str
    requester_display_name: str
    status: str
    created_at: datetime


class FriendOut(BaseModel):
    user_id: UUID
    login: str
    display_name: str
    since: datetime
