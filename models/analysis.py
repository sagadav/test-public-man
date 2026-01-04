from sqlalchemy import Column, Integer, BigInteger, String, TIMESTAMP, text
from models.base import Base

class AnalysisEntry(Base):
    __tablename__ = 'analysis_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    analysis = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))


