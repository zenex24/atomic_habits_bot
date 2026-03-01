import asyncio
from datetime import UTC, datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models.entities import User


def valid_webapp_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            return False
        if not parsed.netloc:
            return False
        if "<" in parsed.netloc or ">" in parsed.netloc:
            return False
        return True
    except Exception:
        return False


if not settings.telegram_bot_token:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN in backend/.env")

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()
scheduler = AsyncIOScheduler()


@dp.message(CommandStart())
async def start(message: Message):
    if valid_webapp_url(settings.telegram_webapp_url):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Открыть Atomic Habits Mini App",
                        web_app=WebAppInfo(url=settings.telegram_webapp_url),
                    )
                ]
            ]
        )
        await message.answer("Запусти Mini App и пройди онбординг.", reply_markup=keyboard)
        return

    await message.answer(
        "URL для Mini App не настроен.\n"
        "Укажи TELEGRAM_WEBAPP_URL в backend/.env (валидный https URL) и перезапусти бота."
    )


async def run_daily_reminders():
    now_utc = datetime.now(UTC)
    async with SessionLocal() as db:
        users = (await db.scalars(select(User))).all()
        for user in users:
            try:
                tz = ZoneInfo(user.timezone)
            except Exception:
                tz = ZoneInfo(settings.default_timezone)

            local_dt = now_utc.astimezone(tz)
            if (
                local_dt.hour == user.daily_reminder_time.hour
                and local_dt.minute == user.daily_reminder_time.minute
                and user.last_reminder_date != local_dt.date()
            ):
                await bot.send_message(
                    user.telegram_id,
                    "Напоминание: сделай маленький шаг по привычке прямо сейчас.",
                )
                user.last_reminder_date = local_dt.date()
        await db.commit()


async def main():
    scheduler.add_job(run_daily_reminders, trigger="interval", minutes=1, max_instances=1)
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
