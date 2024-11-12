from typing import Annotated
from jwt import decode, InvalidTokenError
from fastapi import Depends, Request, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security.api_key import APIKeyHeader

from shortener_app.database import get_db
from shortener_app.user.model import APIUser
from shortener_app.security.exceptions import JsonHTTPException
from shortener_app.config import get_settings
from ...middleware.jwt.errors import AccessError
from ...middleware.jwt.base.token_types import TokenType
from ...middleware.jwt.utils import check_revoked


def __try_to_get_clear_token(authorization_header: str|None) -> str:
    if authorization_header is None:
        raise JsonHTTPException(content=dict(AccessError.get_token_is_not_specified_error()), status_code=400)

    if 'Bearer ' not in authorization_header:
        raise JsonHTTPException(content=dict(AccessError.get_incorrect_auth_header_form_error()), status_code=400)

    return authorization_header.replace('Bearer ', '')


async def check_access_token(
    request: Request,
    # token: Annotated[str, Depends(oauth2_scheme)]
    authorization_header: str = Security(APIKeyHeader(name='Authorization', auto_error=False)),
) -> str:
    # clear_token = token
    clear_token = __try_to_get_clear_token(authorization_header=authorization_header)

    try:
        payload = decode(jwt=clear_token, key=get_settings().jwt_config.secret, algorithms=['HS256', 'RS256'])
        if payload['type'] != TokenType.ACCESS.value:
            raise JsonHTTPException(content=dict(AccessError.get_incorrect_token_type_error()), status_code=403)
    except InvalidTokenError:
        raise JsonHTTPException(content=dict(AccessError.get_invalid_token_error()), status_code=403)

    session: AsyncSession = await anext(get_db())
    if await check_revoked(payload['jti'], session=session):
        raise JsonHTTPException(content=dict(AccessError.get_token_revoked_error()), status_code=403)

    result = await (
        session
        .execute(
            select(APIUser)
            .where(APIUser.id == payload["sub"])
        )
    )
    user = result.scalar_one_or_none()
    # user = await APIUser.filter(id=payload['sub']).first()
    if not user:
        raise JsonHTTPException(content=dict(AccessError.get_token_owner_not_found()), status_code=403)

    request.state.user = user
    request.state.device_id = payload['device_id']
    await session.aclose()
    return authorization_header