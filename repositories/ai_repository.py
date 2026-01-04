"""Repository for AIResponse operations"""
from sqlalchemy import update
from models import AIResponse
from .base import BaseRepository


class AIRepository(BaseRepository):
    """Repository for managing AI responses"""
    
    async def add_ai_response(self, user_id, user_text, ai_response):
        """Add a new AI response and return its ID"""
        async with self.session_maker() as session:
            async with session.begin():
                entry = AIResponse(
                    user_id=user_id,
                    user_text=user_text,
                    ai_response=ai_response
                )
                session.add(entry)
                await session.flush()  # Get entry ID
                return entry.id
    
    async def update_ai_rating(self, response_id, rating: int):
        """Update AI response rating"""
        async with self.session_maker() as session:
            async with session.begin():
                stmt = update(AIResponse).where(
                    AIResponse.id == response_id
                ).values(rating=rating)
                await session.execute(stmt)

