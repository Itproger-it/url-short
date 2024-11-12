import validators
from functools import lru_cache

from fastapi import Depends, APIRouter, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.datastructures import URL
from sqlalchemy.ext.asyncio import AsyncSession

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


@link_route.get("/{url_key}")
async def forward_to_target_url(
        url_key: str,
        request: Request,
        db: AsyncSession = Depends(get_db)
    ):
    if db_url := await crud.get_db_url_by_key(session=db, url_key=url_key):
        await crud.update_db_clicks(db=db, db_url=db_url)
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)


@link_route.post("/decode-shrt-link", response_model=schemas.URLDecode)
async def decode_link(
    url: schemas.URLBase, 
    request: Request,
    ):
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
    ...
    # if db_url := await crud.deactivate_db_url_by_secret_key(db, secret_key=secret_key):
    #     message = f"Successfully deleted shortened URL for '{db_url.target_url}'"
    #     return {"detail": message}
    # else:
    #     raise_not_found(request)