from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GroupCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=64)


class GroupJoinRequest(BaseModel):
    name: str = Field(min_length=3, max_length=64)


class GroupRequestAction(BaseModel):
    action: str = Field(pattern="^(accept|reject)$")


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    owner_id: UUID
    created_at: datetime


class GroupMemberOut(BaseModel):
    user_id: UUID
    login: str
    display_name: str
    role: str
    status: str
    created_at: datetime


class GroupJoinRequestOut(BaseModel):
    user_id: UUID
    login: str
    display_name: str
    created_at: datetime
