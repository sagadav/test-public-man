from sqlalchemy import Column, Integer, BigInteger, String, TIMESTAMP, text
from models.base import Base

class AIResponse(Base):
    __tablename__ = 'ai_responses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    user_text = Column(String, nullable=False)
    ai_response = Column(String, nullable=False)
    rating = Column(Integer, nullable=True)  # 1 для палец вверх, -1 для палец вниз, NULL если не оценено
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))


