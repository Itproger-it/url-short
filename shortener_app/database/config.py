
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from ..config import get_settings

class Model(DeclarativeBase):...

async_engine = create_async_engine(
    get_settings().async_db_url, connect_args={"check_same_thread": False}
)

async_session = async_sessionmaker(
    bind=async_engine,
    autocommit=False, 
    autoflush=False, 
    expire_on_commit=False,
)

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as error:
            await session.rollback()
            raise


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
        

async def delete_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)