from functools import lru_cache

from fastapi import APIRouter, Depends, Request, Security
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shortener_app.security.errors import get_bad_request_error_response
from shortener_app.security.response import ErrorOut, SuccessOut
from shortener_app.config import get_settings
from shortener_app.database.config import get_db
from ..middleware.jwt.service import check_access_token
from ..service import AuthService
from ..middleware.jwt.base.auth import JWTAuth
from .request import UpdateTokensIn, UserCredentialsIn
from .response import TokensOut


auth_router = APIRouter(prefix='/auth', tags=['auth'])

@lru_cache
def get_auth_service() -> AuthService:
    return AuthService(jwt_auth=JWTAuth(config=get_settings().jwt_config))


@auth_router.post(
    path='/register',
    responses={
        200: {'model': TokensOut},
        400: {'model': ErrorOut},
    },
)
async def register(
    request: Request,
    body: UserCredentialsIn,
    auth_service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
) -> TokensOut:
    data, error = await auth_service.register(body=body, session=db)

    if error:
        return get_bad_request_error_response(error=error)

    return data


@auth_router.post(
    path='/login',
    responses={
        200: {'model': TokensOut},
        400: {'model': ErrorOut},
    },
)
async def login(
    request: Request,
    body: UserCredentialsIn,
    auth_service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
) -> TokensOut:
    data, error = await auth_service.login(body=body, session=db)

    if error:
        return get_bad_request_error_response(error=error)

    return data


@auth_router.post(
    path='/logout',
    responses={200: {'model': SuccessOut}},
    dependencies=[Security(check_access_token)],
)
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
) -> SuccessOut:
    await auth_service.logout(
        user=request.state.user, 
        device_id=request.state.device_id, 
        session=db)
    return SuccessOut()


@auth_router.post(
    path='/update-tokens',
    responses={
        200: {'model': TokensOut},
        400: {'model': ErrorOut},
    },
    # dependencies=[Security(check_access_token)],
)
async def update_tokens(
    request: Request,
    body: UpdateTokensIn,
    auth_service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
) -> TokensOut:
    data, error = await auth_service.update_tokens(
        # user=request.state.user, 
        request=request,
        **body.model_dump(), 
        session=db)

    if error:
        return get_bad_request_error_response(error=error)

    return data