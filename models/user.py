from sqlalchemy import Column, Integer, BigInteger, String, TIMESTAMP, text
from models.base import Base

class UserSettings(Base):
    __tablename__ = 'user_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True)
    timezone = Column(String(50), nullable=True)  # Например: 'Europe/Moscow', 'America/New_York'
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))


