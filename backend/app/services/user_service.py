from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search_by_login_prefix(self, query: str, current_user_id: UUID, limit: int = 20) -> list[User]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        statement = (
            select(User)
            .where(
                User.login.ilike(f"{normalized_query}%"),
                User.id != current_user_id,
            )
            .order_by(User.login.asc())
            .limit(limit)
        )
        result = await self.db.scalars(statement)
        return list(result.all())
