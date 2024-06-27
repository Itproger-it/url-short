from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.models import URL


class LinkRepository:

    @classmethod
    async def add_link(
                cls,
                *,
                session: AsyncSession, 
                url: str,
                key: str,
                secret_key: str,
            )-> URL:
        
        db_url = URL(
                key=key,
                target_url=url, 
                secret_key=secret_key)
        session.add(db_url)
        await session.commit()
        await session.refresh(db_url)

        return db_url