from sqlalchemy import Column, Integer, BigInteger, String, TIMESTAMP, text
from models.base import Base

class JournalEntry(Base):
    __tablename__ = 'journal_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    emotion = Column(String(255))
    location = Column(String(255))
    company = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))


