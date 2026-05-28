from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject


DEFAULT_SUBJECTS = [
    "Mathematics",
    "Physics",
    "Computer Science",
    "Biology",
    "Chemistry",
    "History",
    "Literature",
    "Economics",
]


async def seed_subjects(session: AsyncSession) -> None:
    existing = await session.scalars(select(Subject))
    if existing.first() is not None:
        return

    for name in DEFAULT_SUBJECTS:
        session.add(Subject(name=name))
    await session.commit()
