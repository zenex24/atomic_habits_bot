from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.bot.instance import bot
from app.db.models import User
from app.db.session import SessionLocal

scheduler = AsyncIOScheduler()


def should_send_now(user: User, now_utc: datetime) -> bool:
    try:
        user_tz = ZoneInfo(user.timezone)
    except ZoneInfoNotFoundError:
        user_tz = ZoneInfo("UTC")

    local_now = now_utc.astimezone(user_tz)
    current_hm = local_now.strftime("%H:%M")

    if user.reminder_time != current_hm:
        return False

    local_date = local_now.date()
    if user.last_reminded_date == local_date:
        return False

    return True


async def send_daily_reminders() -> None:
    now_utc = datetime.now(tz=ZoneInfo("UTC"))

    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.onboarding_completed.is_(True)))
        users = result.scalars().all()

        for user in users:
            if not should_send_now(user, now_utc):
                continue

            await bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    "Ежедневное напоминание:\n"
                    "1) Выполните минимальную версию привычки сегодня.\n"
                    "2) Отметьте прогресс в mini app.\n"
                    "3) Не пропускайте два дня подряд."
                ),
            )

            try:
                user_tz = ZoneInfo(user.timezone)
            except ZoneInfoNotFoundError:
                user_tz = ZoneInfo("UTC")

            user.last_reminded_date = now_utc.astimezone(user_tz).date()

        await session.commit()


def start_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(send_daily_reminders, "interval", minutes=1, id="daily_reminders", replace_existing=True)
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
