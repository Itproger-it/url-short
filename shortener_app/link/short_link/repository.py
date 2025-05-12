from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shortener_app.database.models import URL, AuthUserUrl, APIUser, UrlMetric
from .dto import UserLinks, UrlMetric as UM


class LinkRepository:

    @classmethod
    async def add_link(
            cls,
            *,
            id: int,
            session: AsyncSession, 
            url: str,
            key: str,
            secret_key: str,
        )-> URL:
        
        db_url = URL(
                id=id,
                key=key,
                target_url=url, 
                secret_key=secret_key,
            )
        session.add(db_url)
        await session.commit()
        await session.refresh(db_url)

        return db_url
    
    @classmethod
    async def get_all_user_urls(
        cls,
        session: AsyncSession,
        user: APIUser,
        ) -> list[UserLinks] | list:
        query = await (
            session
            .execute(
                select(URL)
                .join(AuthUserUrl, URL.id == AuthUserUrl.url_id)
                .where(AuthUserUrl.user_id == user.id, URL.is_active)                
            )
        )

        return [UserLinks.model_validate(data, from_attributes=True) for data in query.scalars().all()]
    
    
    @classmethod
    async def get_url_metric(
        cls,
        session: AsyncSession,
        user: APIUser,
        url: URL,
        ) -> list[UM] | list:
        query = await (
            session
            .execute(
                select(UrlMetric)
                .where(UrlMetric.url_id == url.id)                
            )
        )

        return [UM.model_validate(data, from_attributes=True) for data in query.scalars().all()]

