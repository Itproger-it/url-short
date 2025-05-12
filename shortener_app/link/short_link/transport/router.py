from functools import lru_cache

import validators
from fastapi import Depends, APIRouter, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.datastructures import URL
from sqlalchemy.ext.asyncio import AsyncSession
from user_agents import parse

from shortener_app.security.auth.middleware.jwt.service import check_access_token
from shortener_app.security.auth.service import AuthService
from shortener_app.security.auth.transport.router import get_auth_service

from ..service import ShortLinkServise
from ..errors import raise_not_found, raise_bad_request
from .. import dto as schemas
from shortener_app.database import models, get_db
from shortener_app.config import get_settings


link_route = APIRouter(tags=["short-link"])

@lru_cache
def get_short_link_servise() -> ShortLinkServise:
    return ShortLinkServise()

crud = get_short_link_servise()

def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    base_url = URL(get_settings().base_url)
    admin_endpoint = link_route.url_path_for(
        "administration info", secret_key=db_url.secret_key
    )
    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    return db_url


@link_route.get("/")
async def main():
    return RedirectResponse("docs")


@link_route.post(
    "/url", 
    response_model=schemas.URLInfo
)
async def create_url(
    url: schemas.URLBase, 
    db: AsyncSession = Depends(get_db),
    # authorization_header: str = Security(APIKeyHeader(name='Authorization', auto_error=False))
    ):
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")


    db_url: models.URL = await crud.create_db_url(session=db, url=url)

    return get_admin_info(db_url)


@link_route.post(
    "/auth/url", 
    dependencies=[Security(check_access_token)],
    response_model=schemas.URLInfo
)
async def create_url_u(
    url: schemas.URLBase,
    request: Request,
    db: AsyncSession = Depends(get_db),
    ):
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")


    db_url: models.URL = await crud.create_db_url(session=db, url=url)
    user_link = models.AuthUserUrl(
                            user_id = request.state.user.id,
                            url_id = db_url.id,
                        )
    db.add(user_link)
    await db.commit()

    return get_admin_info(db_url)

@link_route.post(
    "/auth/custom-url", 
    dependencies=[Security(check_access_token)],
    response_model=schemas.URLInfo
)
async def create_url_c_u(
    url: schemas.URLCustom,
    request: Request,
    db: AsyncSession = Depends(get_db),
    ):
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    if await crud.get_db_url_by_key(db, url.name):
        raise_bad_request(message="This name is already in user")
    db_url: models.URL = await crud.create_db_url(session=db, url=url, custom_key=url.name)
    user_link = models.AuthUserUrl(
                            user_id = request.state.user.id,
                            url_id = db_url.id,
                        )
    db.add(user_link)
    await db.commit()

    return get_admin_info(db_url)


@link_route.get("/{url_key}")
async def forward_to_target_url(
        url_key: str,
        request: Request,
        db: AsyncSession = Depends(get_db)
    ):
    user_agent = request.headers.get("User-Agent")
    device = ""
    if request.headers.get("x-forwarded-for"):
        ip = request.headers["x-forwarded-for"].split(",")[0]
    else:
        ip = request.client.host
    if user_agent:
        user_agent = parse(user_agent)
        if user_agent.is_mobile:
            device = "mobile"
        elif user_agent.is_pc:
            device = "desktop"
        else:
            device = "tablet"
    if db_url := await crud.get_db_url_by_key(session=db, url_key=url_key):
        await crud.update_db_clicks(db=db, db_url=db_url, device=device, ip=ip)
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)


@link_route.post(
    "/decode-shrt-link", 
    response_model=schemas.URLDecode,
)
async def decode_link(
    url: schemas.URLBase, 
    request: Request,
    ):
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")
    return await crud.decode_short_link(url=url)


@link_route.get(
    "/admin/{secret_key}",
    name="administration info",
    response_model=schemas.URLInfo,
)
async def get_url_info(
    secret_key: str, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    if db_url := await crud.get_db_url_by_secret_key(db, secret_key=secret_key):
        return get_admin_info(db_url)
    else:
        raise_not_found(request)


@link_route.get(
    path="/u/urls",
    dependencies=[Security(check_access_token)]
)
async def get_user_urls(
    request: Request, 
    db: AsyncSession = Depends(get_db),
    short_link_service: ShortLinkServise = Depends(get_short_link_servise)
):
    return await short_link_service.all_urls(db, request=request)


@link_route.get(
    path="/metric/{url_key}",
    dependencies=[Security(check_access_token)]
)
async def get_url_metric(
    url_key: str,
    request: Request, 
    db: AsyncSession = Depends(get_db),
    short_link_service: ShortLinkServise = Depends(get_short_link_servise)
):
    if db_url := await crud.get_db_url_by_key(session=db, url_key=url_key):
        return await short_link_service.metric_url(db, request=request, url=db_url)
    else:
        raise_not_found(request)


@link_route.delete(
    path="/del-url/{key}",
    dependencies=[Security(check_access_token)]
)
async def delete_url(
    key: str, 
    request: Request, 
    db: AsyncSession = Depends(get_db), 
    auth_service: AuthService = Depends(get_auth_service)
):
    if db_url := await crud.deactivate_db_url_by_secret_key(request, db, key):
        message = f"Successfully deleted shortened URL for '{db_url.target_url}'"
        return {"detail": message}
    else:
        raise_not_found(request)
    