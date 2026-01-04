"""Repository for JournalEntry operations"""
from sqlalchemy import select
from models import JournalEntry
from .base import BaseRepository


class JournalRepository(BaseRepository):
    """Repository for managing journal entries"""
    
    async def add_entry(self, user_id, emotion, location, company):
        """Add a new journal entry"""
        async with self.session_maker() as session:
            async with session.begin():
                entry = JournalEntry(
                    user_id=user_id,
                    emotion=emotion,
                    location=location,
                    company=company
                )
                session.add(entry)
    
    async def get_entries(self, user_id: int, limit: int = 10):
        """Get recent journal entries for a user"""
        async with self.session_maker() as session:
            stmt = select(JournalEntry).where(
                JournalEntry.user_id == user_id
            ).order_by(JournalEntry.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_entries_since(self, user_id: int, since_date):
        """Get journal entries since a specific date"""
        async with self.session_maker() as session:
            stmt = select(JournalEntry).where(
                (JournalEntry.user_id == user_id) & 
                (JournalEntry.created_at >= since_date)
            ).order_by(JournalEntry.created_at.asc())
            result = await session.execute(stmt)
            return result.scalars().all()

