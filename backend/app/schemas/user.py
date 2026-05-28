from uuid import UUID

from pydantic import BaseModel


class UserSearchOut(BaseModel):
    id: UUID
    login: str
    display_name: str
