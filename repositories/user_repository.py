"""Repository for UserSettings operations"""
from typing import Optional, List
from sqlalchemy import select, distinct
from models import UserSettings, GoalEntry
from .base import BaseRepository


class UserRepository(BaseRepository):
    """Repository for managing user settings"""

    async def get_user_settings(self, user_id: int) -> Optional[UserSettings]:
        """Get user settings by user ID"""
        async with self.session_maker() as session:
            stmt = select(UserSettings).where(
                UserSettings.user_id == user_id
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def set_user_timezone(self, user_id: int, timezone: str) -> None:
        """Set or update user timezone (upsert operation)"""
        async with self.session_maker() as session:
            async with session.begin():
                stmt = select(UserSettings).where(
                    UserSettings.user_id == user_id
                )
                result = await session.execute(stmt)
                existing = result.scalars().first()

                if existing:
                    existing.timezone = timezone
                else:
                    settings = UserSettings(
                        user_id=user_id,
                        timezone=timezone
                    )
                    session.add(settings)

    async def get_all_users_with_timezone(self) -> List[UserSettings]:
        """Get all users with timezone set"""
        async with self.session_maker() as session:
            stmt = select(UserSettings).where(
                UserSettings.timezone.isnot(None)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    def _create_default_settings(self, user_id: int) -> UserSettings:
        """Factory method to create UserSettings with default values"""
        return UserSettings(
            user_id=user_id,
            timezone=None
        )

    async def get_all_users_with_goals(self) -> List[UserSettings]:
        """
        Get all users who have goals.
        Returns UserSettings for each user
        (creates default settings if not exists).
        """
        async with self.session_maker() as session:
            stmt_goals = select(distinct(GoalEntry.user_id))
            result_goals = await session.execute(stmt_goals)
            user_ids = list(result_goals.scalars().all())

            if not user_ids:
                return []

            stmt_settings = select(UserSettings).where(
                UserSettings.user_id.in_(user_ids)
            )
            result_settings = await session.execute(stmt_settings)
            existing_settings = {
                settings.user_id: settings
                for settings in result_settings.scalars().all()
            }

            return [
                existing_settings.get(user_id)
                or self._create_default_settings(user_id)
                for user_id in user_ids
            ]
