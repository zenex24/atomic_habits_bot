import json

import httpx

from app.config import settings


def build_mentor_system_prompt(mode: str) -> str:
    mode_map = {
        "soft": "Ты мягкий и поддерживающий наставник.",
        "neutral": "Ты спокойный и прагматичный наставник.",
        "strict": "Ты строгий и прямой наставник, но без унижения.",
    }
    return (
        f"{mode_map.get(mode, mode_map['neutral'])} "
        "Контекст: методика из книги Atomic Habits, только практичные шаги, коротко, по-русски."
    )


async def chat_completion(*, system_prompt: str, messages: list[dict], max_tokens: int = 450) -> dict:
    if not settings.openrouter_api_key:
        return {
            "content": "OpenRouter ключ не задан. Добавь OPENROUTER_API_KEY в .env.",
            "prompt_tokens": 0,
            "completion_tokens": 0,
        }

    payload = {
        "model": settings.openrouter_model,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_site_url,
        "X-Title": settings.openrouter_site_name,
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions", headers=headers, content=json.dumps(payload)
        )
    response.raise_for_status()
    data = response.json()
    usage = data.get("usage", {})
    return {
        "content": data["choices"][0]["message"]["content"],
        "prompt_tokens": int(usage.get("prompt_tokens", 0)),
        "completion_tokens": int(usage.get("completion_tokens", 0)),
    }
