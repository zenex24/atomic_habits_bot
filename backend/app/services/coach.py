from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings

TONE_MAP = {
    "friendly": "дружелюбный, поддерживающий",
    "neutral": "нейтральный, деловой и ясный",
    "strict": "строгий, требовательный, но уважительный",
}


SYSTEM_PROMPT = (
    "Вы наставник по формированию привычек. Основа ваших рекомендаций - подход книги "
    "'Atomic Habits' (Джеймс Клир): 1) делать привычку очевидной, 2) привлекательной, "
    "3) простой, 4) удовлетворяющей. Для избавления от плохой привычки применяйте обратные шаги. "
    "Давайте конкретные действия на сегодня и ближайшую неделю, коротко и практично. "
    "Учитывайте прогресс пользователя и не повторяйтесь. Отвечайте только на русском языке."
)


async def ask_openrouter(
    user_profile: dict[str, Any],
    history: list[dict[str, str]],
    message: str,
) -> str:
    settings = get_settings()
    tone = TONE_MAP.get(user_profile.get("mentor_tone", "neutral"), "нейтральный, деловой и ясный")

    profile_context = (
        f"Профиль пользователя: имя={user_profile.get('display_name')}; "
        f"цель={user_profile.get('goal_type')}; привычка={user_profile.get('habit_name')}; "
        f"категория={user_profile.get('habit_category')}; детали={user_profile.get('habit_details')}; "
        f"мотивация={user_profile.get('motivation')}; тон={tone}."
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT + " " + profile_context}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    payload = {
        "model": settings.openrouter_model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500,
    }

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    return data["choices"][0]["message"]["content"].strip()
