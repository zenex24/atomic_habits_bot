from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


Tone = Literal["friendly", "neutral", "strict"]
GoalType = Literal["build", "break"]


class BootstrapResponse(BaseModel):
    user: dict
    onboarding_completed: bool
    home: dict


class OnboardingRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=128)
    goal_type: GoalType
    habit_category: str = Field(min_length=2, max_length=64)
    habit_name: str = Field(min_length=2, max_length=128)
    habit_details: str = Field(min_length=2, max_length=2000)
    motivation: str = Field(min_length=2, max_length=2000)
    baseline_frequency: str = Field(min_length=2, max_length=128)
    mentor_tone: Tone
    reminder_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    timezone: str = Field(min_length=2, max_length=64)
    privacy_accepted: bool


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)


class ChatResponse(BaseModel):
    reply: str
    remaining_today: int


class PlanItemCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    weekday: int | None = Field(default=None, ge=0, le=6)


class PlanItemUpdate(BaseModel):
    is_done: bool


class PlanItemOut(BaseModel):
    id: int
    title: str
    description: str | None
    weekday: int | None
    is_done: bool


class HabitCheckinRequest(BaseModel):
    completed: bool
    note: str | None = Field(default=None, max_length=1000)


class HabitCheckinOut(BaseModel):
    streak_days: int
    best_streak: int
    log_date: date


class ChallengeOut(BaseModel):
    id: int
    title: str
    description: str
    duration_days: int
    points: int
    joined: bool
    progress_days: int
    is_completed: bool


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=128)
    mentor_tone: Tone | None = None
    reminder_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    timezone: str | None = Field(default=None, min_length=2, max_length=64)
    habit_details: str | None = Field(default=None, max_length=2000)


class ProfileOut(BaseModel):
    display_name: str | None
    mentor_tone: str
    reminder_time: str
    timezone: str
    goal_type: str | None
    habit_name: str | None
    habit_category: str | None
    habit_details: str | None
    motivation: str | None
    baseline_frequency: str | None
    streak_days: int
    best_streak: int


class AdminMetricsOut(BaseModel):
    total_users: int
    onboarding_completed_users: int
    dau: int
    avg_streak: float
    completion_rate_7d: float
    retention_d1: float
    retention_d7: float


class AdminUserOut(BaseModel):
    telegram_id: int
    display_name: str | None
    goal_type: str | None
    habit_name: str | None
    onboarding_completed: bool
    streak_days: int
    last_active_at: str
