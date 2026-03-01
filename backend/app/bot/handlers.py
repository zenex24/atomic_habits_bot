from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from app.core.config import get_settings

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    settings = get_settings()

    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть Atomic Habits Mini App",
                    web_app=WebAppInfo(url=settings.webapp_url),
                )
            ]
        ]
    )

    reply_keyboard = ReplyKeyboardMarkup(
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
        "Добро пожаловать. Откройте mini app кнопкой ниже.",
        reply_markup=inline_keyboard,
    )
    await message.answer(
        "Если inline-кнопка не сработала, используйте кнопку в клавиатуре.",
        reply_markup=reply_keyboard,
    )


@router.message(F.text == "/help")
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Команды:\n/start - открыть mini app\n"
        "Напоминания будут приходить автоматически 1 раз в день."
    )
