import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class HabitType(str, enum.Enum):
    good = "good"
    bad = "bad"


class MentorMode(str, enum.Enum):
    soft = "soft"
    neutral = "neutral"
    strict = "strict"


class PlanFrequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"


class ChallengeKind(str, enum.Enum):
    seven = "seven"
    fourteen = "fourteen"
    thirty = "thirty"
    no_skip = "no_skip"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="User")
    language: Mapped[str] = mapped_column(String(8), default="ru")
    timezone: Mapped[str] = mapped_column(String(120), default="Europe/Moscow")
    mentor_mode: Mapped[MentorMode] = mapped_column(String(20), default=MentorMode.neutral.value)
    onboarding_done: Mapped[bool] = mapped_column(Boolean, default=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_reminder_time: Mapped[time] = mapped_column(Time, default=time(hour=9, minute=0))
    last_reminder_date: Mapped[date] = mapped_column(Date, default=date.today)
    daily_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    daily_token_date: Mapped[date] = mapped_column(Date, default=date.today)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    habits: Mapped[list["Habit"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    plans: Mapped[list["PlanItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    challenges: Mapped[list["Challenge"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text, default="")
    type: Mapped[HabitType] = mapped_column(String(20))
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    target_mode: Mapped[str] = mapped_column(String(60), default="maintain")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="habits")


class PlanItem(Base):
    __tablename__ = "plan_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    details: Mapped[str] = mapped_column(Text, default="")
    frequency: Mapped[PlanFrequency] = mapped_column(String(20))
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    weekday: Mapped[str] = mapped_column(String(20), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="plans")


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[ChallengeKind] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(120))
    days_total: Mapped[int] = mapped_column(Integer, default=7)
    current_day: Mapped[int] = mapped_column(Integer, default=1)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    misses: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="challenges")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="messages")
