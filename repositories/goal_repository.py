"""Repository for GoalEntry operations"""
from sqlalchemy import select, update, delete, cast, Date
from models import GoalEntry
from .base import BaseRepository


class GoalRepository(BaseRepository):
    """Repository for managing goal entries"""
    
    async def add_goal(self, user_id, goal_text, result_text, target_date):
        """Add a new goal entry"""
        async with self.session_maker() as session:
            async with session.begin():
                entry = GoalEntry(
                    user_id=user_id,
                    goal_text=goal_text,
                    result_text=result_text,
                    target_date=target_date
                )
                session.add(entry)
    
    async def get_goals(self, user_id: int, limit: int = 10):
        """Get recent goals for a user"""
        async with self.session_maker() as session:
            stmt = select(GoalEntry).where(
                GoalEntry.user_id == user_id
            ).order_by(GoalEntry.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_active_goals_for_date(self, target_date):
        """Get all active goals for a specific date"""
        async with self.session_maker() as session:
            stmt = select(GoalEntry).where(
                (cast(GoalEntry.target_date, Date) == target_date.date()) &
                (GoalEntry.is_completed == 0)
            )
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_user_goal_for_date(self, user_id: int, target_date):
        """Get active goal for a user on a specific date"""
        async with self.session_maker() as session:
            stmt = select(GoalEntry).where(
                (GoalEntry.user_id == user_id) &
                (cast(GoalEntry.target_date, Date) == target_date.date()) &
                (GoalEntry.is_completed == 0)
            ).order_by(GoalEntry.created_at.desc()).limit(1)
            result = await session.execute(stmt)
            return result.scalars().first()
    
    async def delete_goal(self, goal_id: int):
        """Delete a goal by ID"""
        async with self.session_maker() as session:
            async with session.begin():
                stmt = delete(GoalEntry).where(GoalEntry.id == goal_id)
                await session.execute(stmt)
    
    async def update_goal_status(self, goal_id, is_completed: int):
        """Update goal completion status"""
        async with self.session_maker() as session:
            async with session.begin():
                stmt = update(GoalEntry).where(
                    GoalEntry.id == goal_id
                ).values(is_completed=is_completed)
                await session.execute(stmt)

