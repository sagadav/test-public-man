from sqlalchemy import Column, Integer, BigInteger, String, TIMESTAMP, text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class JournalEntry(Base):
    __tablename__ = 'journal_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    emotion = Column(String(255))
    location = Column(String(255))
    company = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

class AnalysisEntry(Base):
    __tablename__ = 'analysis_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    analysis = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

class GoalEntry(Base):
    __tablename__ = 'goal_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    goal_text = Column(String, nullable=False)
    result_text = Column(String)
    target_date = Column(TIMESTAMP, nullable=False)
    is_completed = Column(Integer, server_default=text('0'))
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

class AIResponse(Base):
    __tablename__ = 'ai_responses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    user_text = Column(String, nullable=False)
    ai_response = Column(String, nullable=False)
    rating = Column(Integer, nullable=True)  # 1 для палец вверх, -1 для палец вниз, NULL если не оценено
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))


class UserSettings(Base):
    __tablename__ = 'user_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True)
    timezone = Column(String(50), nullable=True)  # Например: 'Europe/Moscow', 'America/New_York'
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))