from typing import Annotated, AsyncGenerator
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from ..config import get_settings


str_36 = Annotated[str, 36]
class Model(DeclarativeBase):
    type_annotation_map = {
        str_36: String(36)
    }

async_engine = create_async_engine(
    get_settings().async_db_url, connect_args={"check_same_thread": False}
)

async_session = async_sessionmaker(
    bind=async_engine,
    autocommit=False, 
    autoflush=False, 
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
        # try:
        #     yield session
        #     # await session.commit()
        #     # await session.close()
        # except SQLAlchemyError as error:
        #     await session.rollback()
        #     raise


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
        

async def delete_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)