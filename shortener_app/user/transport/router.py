from fastapi import APIRouter, Request, Security, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from shortener_app.user.dto import UserProfileDTO

from ..service import MeService
from .response import UserProfileOut
from shortener_app.security.auth.middleware.jwt.service import check_access_token
from shortener_app.database import models, get_db



me_router = APIRouter(prefix='/me', tags=['me'], 
                      dependencies=[Security(check_access_token)]
                      )


def get_me_service() -> MeService:
    return MeService()


@me_router.head("/")
async def get_auth(request: Request, me_service: MeService = Depends(get_me_service)) -> None:
    return


@me_router.get("/me")
async def get_me(request: Request, me_service: MeService = Depends(get_me_service)) -> UserProfileDTO:
    return me_service.get_me(user=request.state.user)