from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.models import Challenge
from app.db.session import engine

DEFAULT_CHALLENGES = [
    {
        "title": "7 дней раннего сна",
        "description": "Ложиться спать до выбранного времени 7 дней подряд.",
        "duration_days": 7,
        "points": 70,
    },
    {
        "title": "Без дешевого дофамина",
        "description": "Сократить короткие отвлечения: минимум 2 часа фокус-блока ежедневно.",
        "duration_days": 10,
        "points": 100,
    },
    {
        "title": "Минимум 20 минут спорта",
        "description": "Каждый день не менее 20 минут физической активности.",
        "duration_days": 14,
        "points": 140,
    },
]


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_challenges(session: AsyncSession) -> None:
    existing = await session.execute(select(Challenge.id).limit(1))
    if existing.scalar_one_or_none() is not None:
        return

    session.add_all([Challenge(**item) for item in DEFAULT_CHALLENGES])
    await session.commit()
