"""Database connection initialization"""
import os
import urllib.parse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()


async def init_session_maker():
    """Initialize and return async session maker for database"""
    user = urllib.parse.quote_plus(os.getenv("DB_USER"))
    password = urllib.parse.quote_plus(os.getenv("DB_PASSWORD"))
    host = os.getenv("DB_HOST")
    name = os.getenv("DB_NAME")
    port = os.getenv("DB_PORT")
    
    db_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
    engine = create_async_engine(db_url, echo=True)
    return async_sessionmaker(engine, expire_on_commit=False)

