"""Repository for UserSettings operations"""
from sqlalchemy import select, update, distinct
from models import UserSettings, GoalEntry
from .base import BaseRepository


class UserSettingsStub:
    """Stub for UserSettings for users without settings"""
    def __init__(self, user_id):
        self.user_id = user_id
        self.timezone = None


class UserRepository(BaseRepository):
    """Repository for managing user settings"""
    
    async def get_user_settings(self, user_id: int):
        """Get user settings by user ID"""
        async with self.session_maker() as session:
            stmt = select(UserSettings).where(
                UserSettings.user_id == user_id
            ).limit(1)
            result = await session.execute(stmt)
            return result.scalars().first()
    
    async def set_user_timezone(self, user_id: int, timezone: str):
        """Set or update user timezone (upsert operation)"""
        async with self.session_maker() as session:
            async with session.begin():
                # Check if settings exist
                stmt_check = select(UserSettings).where(
                    UserSettings.user_id == user_id
                )
                result = await session.execute(stmt_check)
                existing = result.scalars().first()
                
                if existing:
                    # Update existing record
                    stmt = update(UserSettings).where(
                        UserSettings.user_id == user_id
                    ).values(timezone=timezone)
                    await session.execute(stmt)
                else:
                    # Create new record
                    settings = UserSettings(
                        user_id=user_id,
                        timezone=timezone
                    )
                    session.add(settings)
    
    async def get_all_users_with_timezone(self):
        """Get all users with timezone set"""
        async with self.session_maker() as session:
            stmt = select(UserSettings).where(
                UserSettings.timezone.isnot(None)
            )
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_all_users_with_goals(self):
        """
        Get all users who have goals.
        Returns UserSettings for each user (creates stub if not exists).
        """
        async with self.session_maker() as session:
            # Get all unique user_ids from GoalEntry
            stmt_goals = select(distinct(GoalEntry.user_id))
            result_goals = await session.execute(stmt_goals)
            user_ids = list(result_goals.scalars().all())
            
            if not user_ids:
                return []
            
            # Get UserSettings for these users
            stmt_settings = select(UserSettings).where(
                UserSettings.user_id.in_(user_ids)
            )
            result_settings = await session.execute(stmt_settings)
            existing_settings = {
                settings.user_id: settings 
                for settings in result_settings.scalars().all()
            }
            
            # Create UserSettings or stub for users without settings
            all_settings = []
            for user_id in user_ids:
                if user_id in existing_settings:
                    all_settings.append(existing_settings[user_id])
                else:
                    # Create stub for user without settings
                    # timezone_service will handle this and use default UTC+5
                    all_settings.append(UserSettingsStub(user_id))
            
            return all_settings

