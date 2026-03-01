from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

from app.core.config import get_settings

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    settings = get_settings()
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Открыть Atomic Habits Mini App",
                    web_app=WebAppInfo(url=settings.webapp_url),
                )
            ]
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "Добро пожаловать. Откройте mini app и начните работу с привычками.",
        reply_markup=keyboard,
    )


@router.message(F.text == "/help")
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Команды:\n/start - открыть mini app\n"
        "Напоминания будут приходить автоматически 1 раз в день."
    )
