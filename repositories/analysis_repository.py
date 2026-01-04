"""Repository for AnalysisEntry operations"""
from sqlalchemy import select
from models import AnalysisEntry
from .base import BaseRepository


class AnalysisRepository(BaseRepository):
    """Repository for managing analysis entries"""
    
    async def add_analysis(self, user_id, analysis_text):
        """Add a new analysis entry"""
        async with self.session_maker() as session:
            async with session.begin():
                entry = AnalysisEntry(
                    user_id=user_id,
                    analysis=analysis_text
                )
                session.add(entry)
    
    async def get_latest_analysis(self, user_id: int):
        """Get the latest analysis entry for a user"""
        async with self.session_maker() as session:
            stmt = select(AnalysisEntry).where(
                AnalysisEntry.user_id == user_id
            ).order_by(AnalysisEntry.created_at.desc()).limit(1)
            result = await session.execute(stmt)
            return result.scalars().first()

