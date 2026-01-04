from sqlalchemy import Column, Integer, BigInteger, String, TIMESTAMP, text
from models.base import Base

class GoalEntry(Base):
    __tablename__ = 'goal_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    goal_text = Column(String, nullable=False)
    result_text = Column(String)
    target_date = Column(TIMESTAMP, nullable=False)
    is_completed = Column(Integer, server_default=text('0'))
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))


