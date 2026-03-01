from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import HabitLog, User


async def get_admin_metrics(session: AsyncSession) -> dict:
    today = date.today()
    day_1 = today - timedelta(days=1)
    day_7 = today - timedelta(days=7)

    total_users = await session.scalar(select(func.count(User.id))) or 0
    onboarding_completed_users = (
        await session.scalar(select(func.count(User.id)).where(User.onboarding_completed.is_(True))) or 0
    )

    dau = (
        await session.scalar(
            select(func.count(User.id)).where(func.date(User.last_active_at) == today.isoformat())
        )
        or 0
    )

    avg_streak = float((await session.scalar(select(func.avg(User.streak_days))) or 0.0) or 0.0)

    logs_7d = (
        await session.scalar(
            select(func.count(HabitLog.id)).where(HabitLog.log_date >= day_7)
        )
        or 0
    )
    completed_7d = (
        await session.scalar(
            select(func.count(HabitLog.id)).where(and_(HabitLog.log_date >= day_7, HabitLog.completed.is_(True)))
        )
        or 0
    )
    completion_rate_7d = (completed_7d / logs_7d * 100.0) if logs_7d else 0.0

    users_yesterday = (
        await session.scalar(select(func.count(User.id)).where(func.date(User.created_at) <= day_1.isoformat()))
        or 0
    )
    active_d1 = (
        await session.scalar(select(func.count(User.id)).where(func.date(User.last_active_at) == today.isoformat())) or 0
    )
    retention_d1 = (active_d1 / users_yesterday * 100.0) if users_yesterday else 0.0

    users_week_ago = (
        await session.scalar(select(func.count(User.id)).where(func.date(User.created_at) <= day_7.isoformat()))
        or 0
    )
    active_d7 = (
        await session.scalar(select(func.count(User.id)).where(func.date(User.last_active_at) >= day_7.isoformat())) or 0
    )
    retention_d7 = (active_d7 / users_week_ago * 100.0) if users_week_ago else 0.0

    return {
        "total_users": int(total_users),
        "onboarding_completed_users": int(onboarding_completed_users),
        "dau": int(dau),
        "avg_streak": round(avg_streak, 2),
        "completion_rate_7d": round(completion_rate_7d, 2),
        "retention_d1": round(retention_d1, 2),
        "retention_d7": round(retention_d7, 2),
    }
