# src/crud.py

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select

from ..schema import schemas

from ..database import models

from .. import keygen

from ..repository.link_repository import LinkRepository


async def create_db_url(session: AsyncSession, url: schemas.URLBase) -> models.URL:
    key = await keygen.create_unique_random_key(session)
    secret_key = f"{key}_{keygen.create_random_key(length=8)}"
    db_url = await LinkRepository.add_link(
                            session=session,
                            url=url.target_url,
                            key=key,
                            secret_key=secret_key,
                            )
    return db_url


async def get_db_url_by_key(session: AsyncSession, url_key: str) -> models.URL|None:
    query = (
        select(models.URL)
        .where(models.URL.key == url_key, models.URL.is_active)
        .limit(1))
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_db_url_by_secret_key(session: AsyncSession, secret_key: str) -> models.URL|None:
    query = (
        select(models.URL)
        .where(models.URL.secret_key == secret_key, models.URL.is_active)
        .limit(1))
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def update_db_clicks(db: AsyncSession, db_url: schemas.URL) -> models.URL:
    db_url.clicks += 1
    await db.commit()
    await db.refresh(db_url)
    return db_url


async def deactivate_db_url_by_secret_key(db: AsyncSession, secret_key: str) -> models.URL|None:
    db_url = await get_db_url_by_secret_key(db, secret_key)
    if db_url:
        db_url.is_active = False
        await db.commit()
        await db.refresh(db_url)
    return db_url