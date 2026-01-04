"""Base repository class"""
from abc import ABC
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


class BaseRepository(ABC):
    """Base class for all repositories"""
    
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

