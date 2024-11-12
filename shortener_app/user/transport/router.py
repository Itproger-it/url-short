from fastapi import APIRouter, Request, Security, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..service import MeService
from .response import UserProfileOut
from shortener_app.security.auth.middleware.jwt.service import check_access_token
from shortener_app.database import models, get_db



me_router = APIRouter(prefix='/me', tags=['me'], 
                      dependencies=[Security(check_access_token)]
                      )


def get_me_service() -> MeService:
    return MeService()


@me_router.get("/me")
async def get_me(request: Request, me_service: MeService = Depends(get_me_service)) -> None:
    return me_service.get_me(user=request.state.user)


# @me_router.get("create-user")
# async def create(session: AsyncSession = Depends(get_db)):
#     user = models.APIUser()