import validators
from fastapi import Depends, APIRouter, HTTPException, Request, status

from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.datastructures import URL
from sqlalchemy.ext.asyncio import AsyncSession

from ..schema import schemas
from ..service import crud
from ..database import models, get_db
from ..config import get_settings



link_route = APIRouter()


async def raise_bad_request(message: str):
    raise HTTPException(status_code=400, detail=message)


def raise_not_found(request: Request):
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)


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


@link_route.post("/url", response_model=schemas.URLInfo)
async def create_url(url: schemas.URLBase, db: AsyncSession = Depends(get_db)):
    if not validators.url(url.target_url):
        await raise_bad_request(message="Your provided URL is not valid")


    db_url: models.URL = await crud.create_db_url(session=db, url=url)

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


@link_route.get(
    "/admin/{secret_key}",
    name="administration info",
    response_model=schemas.URLInfo,
)
async def get_url_info(
    secret_key: str, request: Request, db: AsyncSession = Depends(get_db)
):
    if db_url := await crud.get_db_url_by_secret_key(db, secret_key=secret_key):
        return get_admin_info(db_url)
    else:
        raise_not_found(request)


@link_route.delete("/admin/{secret_key}")
async def delete_url(
    secret_key: str, request: Request, db: AsyncSession = Depends(get_db)
):
    if db_url := await crud.deactivate_db_url_by_secret_key(db, secret_key=secret_key):
        message = f"Successfully deleted shortened URL for '{db_url.target_url}'"
        return {"detail": message}
    else:
        raise_not_found(request)