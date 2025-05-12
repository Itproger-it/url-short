import datetime
import secrets
import string
from functools import lru_cache

import aiohttp
from fastapi import Request, Security
from fastapi.security import APIKeyHeader
from snowflake import SnowflakeGenerator
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from shortener_app.link.short_link.model import URL, UrlMetric
from shortener_app.security.auth.middleware.jwt.service import __try_to_get_clear_token


from . import dto as schemas
from shortener_app.config import get_settings
from shortener_app.database import models
from .repository import LinkRepository

@lru_cache
def get_snowflake_id()->int:
    return SnowflakeGenerator(get_settings().snowflake_code)


class ShortLinkServise:

    async def user_is_auth(
        request: Request,
        authorization_header: str = Security(APIKeyHeader(name='Authorization', auto_error=False)),
    ) -> str:
        if authorization_header and 'Bearer ' in authorization_header:
            ...

    def create_random_key(self, length: int = 6) -> str:
        chars = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(chars) for _ in range(length))


    async def create_unique_random_key(self, db: Session) -> str:
        key = self.create_random_key()
        while await self.get_db_url_by_key(db, key):
            key = self.create_random_key()
        return key


    async def create_db_url(
            self, 
            session: AsyncSession, 
            url: schemas.URLBase,
            custom_key: str = ""
        ) -> models.URL:
        id = self.__gen_snowflake_id()
        if custom_key and custom_key.isalnum():
            key = custom_key
        else: key = await self.create_unique_random_key(session)
        secret_key = f"{key}_{self.create_random_key(length=8)}"
        db_url = await (
            LinkRepository
            .add_link(
                id=id,
                session=session,
                url=url.target_url,
                key=key,
                secret_key=secret_key,
            )
        )
        return db_url
    

    def __gen_snowflake_id(self) -> int:
        return next(get_snowflake_id())
    

    async def decode_short_link(
            self, 
            url: schemas.URLBase,
        ) -> schemas.URLBase:
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as sessn:
                async with sessn.get(url.target_url, allow_redirects=True) as response:
                    return schemas.URLDecode(url=str(response.url))
                
        except aiohttp.ClientConnectorError:
            return schemas.URLDecode(url = url.target_url)
        
        except Exception as e:
            return None


    async def get_db_url_by_key(
            self, 
            session: AsyncSession, 
            url_key: str,
        ) -> models.URL|None:

        result = await (
            session
            .execute(
                select(models.URL)
                .where(
                    models.URL.key == url_key, 
                    models.URL.is_active)
                .limit(1)
            )
        )
        return result.scalar_one_or_none()


    async def get_db_url_by_secret_key(
            self,
            user: models.APIUser,
            session: AsyncSession, 
            secret_key: str,
        ) -> models.URL|None:

        result = await (
            session
            .execute(
                select(models.URL)
                .join(models.AuthUserUrl, models.URL.id == models.AuthUserUrl.url_id)
                .where(
                    models.AuthUserUrl.user_id == user.id,
                    models.URL.secret_key == secret_key, 
                    models.URL.is_active)
                .limit(1)
            )
        )
        return result.scalar_one_or_none()


    async def update_db_clicks(
            self, 
            db: AsyncSession, 
            db_url: schemas.URL,
            device: str,
            ip: str,
        ) -> models.URL:
        
        db_url.clicks += 1
        await db.commit()
        await db.refresh(db_url)

        metric = UrlMetric(
            url_id=db_url.id,
            device=device,
            ip=ip,
            date=datetime.datetime.now().strftime('%Y-%m-%d'),
        )
        db.add(metric)
        await db.commit()

        return db_url
    
    async def all_urls(
            self,
            db: AsyncSession,
            request: Request,
            ):
        
        return await (
            LinkRepository
            .get_all_user_urls(
                session=db, 
                user=request.state.user,
                )
            )
    
    async def metric_url(
            self,
            db: AsyncSession,
            request: Request,
            url: URL,
            ):
        
        return await (
            LinkRepository
            .get_url_metric(
                session=db, 
                user=request.state.user,
                url=url,
                )
            )

    async def deactivate_db_url_by_secret_key(
            self,
            request: Request,
            db: AsyncSession, 
            secret_key: str,
        ) -> models.URL|None:
        
        db_url = await self.get_db_url_by_secret_key(request.state.user, db, secret_key)
        if db_url:
            db_url.is_active = False
            await db.commit()
            await db.refresh(db_url)
        return db_url