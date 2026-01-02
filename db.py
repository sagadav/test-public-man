import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from dotenv import load_dotenv
from models import (
    JournalEntry,
    AnalysisEntry,
    GoalEntry,
    AIResponse,
    UserSettings
)

load_dotenv()

import urllib.parse

async def init_session_maker():
    user = urllib.parse.quote_plus(os.getenv("DB_USER"))
    password = urllib.parse.quote_plus(os.getenv("DB_PASSWORD"))
    host = os.getenv("DB_HOST")
    name = os.getenv("DB_NAME")
    
    port = os.getenv("DB_PORT")
    
    db_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
    engine = create_async_engine(db_url, echo=True)
    return async_sessionmaker(engine, expire_on_commit=False)

async def add_entry(session_maker: async_sessionmaker[AsyncSession], user_id, emotion, location, company):
    async with session_maker() as session:
        async with session.begin():
            entry = JournalEntry(
                user_id=user_id,
                emotion=emotion,
                location=location,
                company=company
            )
            session.add(entry)
        # Commit happens automatically on exit from session.begin() block

async def get_entries(session_maker: async_sessionmaker[AsyncSession], user_id: int):
    async with session_maker() as session:
        stmt = select(JournalEntry).where(JournalEntry.user_id == user_id).order_by(JournalEntry.created_at.desc()).limit(10)
        result = await session.execute(stmt)
        return result.scalars().all()

async def add_analysis(session_maker: async_sessionmaker[AsyncSession], user_id, analysis_text):
    async with session_maker() as session:
        async with session.begin():
            # from models import AnalysisEntry # Import here or top level
            entry = AnalysisEntry(
                user_id=user_id,
                analysis=analysis_text
            )
            session.add(entry)

async def get_entries_since(session_maker: async_sessionmaker[AsyncSession], user_id: int, since_date):
    async with session_maker() as session:
        # Import models inside if needed or rely on top level
        stmt = select(JournalEntry).where(
            (JournalEntry.user_id == user_id) & 
            (JournalEntry.created_at >= since_date)
        ).order_by(JournalEntry.created_at.asc())
        result = await session.execute(stmt)
        return result.scalars().all()

async def get_latest_analysis(session_maker: async_sessionmaker[AsyncSession], user_id: int):
    async with session_maker() as session:
        stmt = select(AnalysisEntry).where(AnalysisEntry.user_id == user_id).order_by(AnalysisEntry.created_at.desc()).limit(1)
        result = await session.execute(stmt)
        return result.scalars().first()

async def add_goal(session_maker: async_sessionmaker[AsyncSession], user_id, goal_text, result_text, target_date):
    async with session_maker() as session:
        async with session.begin():
            entry = GoalEntry(
                user_id=user_id,
                goal_text=goal_text,
                result_text=result_text,
                target_date=target_date
            )
            session.add(entry)

async def get_goals(session_maker: async_sessionmaker[AsyncSession], user_id: int):
    async with session_maker() as session:
        stmt = select(GoalEntry).where(GoalEntry.user_id == user_id).order_by(GoalEntry.created_at.desc()).limit(10)
        result = await session.execute(stmt)
        return result.scalars().all()

async def get_active_goals_for_date(session_maker: async_sessionmaker[AsyncSession], target_date):
    from sqlalchemy import cast, Date
    async with session_maker() as session:
        stmt = select(GoalEntry).where(
            (cast(GoalEntry.target_date, Date) == target_date.date()) &
            (GoalEntry.is_completed == 0)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

async def update_goal_status(session_maker: async_sessionmaker[AsyncSession], goal_id, is_completed: int):
    from sqlalchemy import update
    async with session_maker() as session:
        async with session.begin():
            stmt = update(GoalEntry).where(GoalEntry.id == goal_id).values(is_completed=is_completed)
            await session.execute(stmt)

async def add_ai_response(session_maker: async_sessionmaker[AsyncSession], user_id, user_text, ai_response):
    async with session_maker() as session:
        async with session.begin():
            entry = AIResponse(
                user_id=user_id,
                user_text=user_text,
                ai_response=ai_response
            )
            session.add(entry)
            await session.flush()  # Получаем id записи
            return entry.id

async def update_ai_rating(session_maker: async_sessionmaker[AsyncSession], response_id, rating: int):
    from sqlalchemy import update
    async with session_maker() as session:
        async with session.begin():
            stmt = update(AIResponse).where(AIResponse.id == response_id).values(rating=rating)
            await session.execute(stmt)

async def get_user_settings(session_maker: async_sessionmaker[AsyncSession], user_id: int):
    async with session_maker() as session:
        stmt = select(UserSettings).where(UserSettings.user_id == user_id).limit(1)
        result = await session.execute(stmt)
        return result.scalars().first()

async def set_user_timezone(session_maker: async_sessionmaker[AsyncSession], user_id: int, timezone: str):
    from sqlalchemy import update
    async with session_maker() as session:
        async with session.begin():
            # Проверяем, существует ли запись в текущей сессии
            stmt_check = select(UserSettings).where(UserSettings.user_id == user_id)
            result = await session.execute(stmt_check)
            existing = result.scalars().first()
            
            if existing:
                # Обновляем существующую запись
                stmt = update(UserSettings).where(
                    UserSettings.user_id == user_id
                ).values(timezone=timezone)
                await session.execute(stmt)
            else:
                # Создаем новую запись
                settings = UserSettings(
                    user_id=user_id,
                    timezone=timezone
                )
                session.add(settings)

async def get_all_users_with_timezone(session_maker: async_sessionmaker[AsyncSession]):
    """Получает всех пользователей с установленным часовым поясом"""
    async with session_maker() as session:
        stmt = select(UserSettings).where(UserSettings.timezone.isnot(None))
        result = await session.execute(stmt)
        return result.scalars().all()
