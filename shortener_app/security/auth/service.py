from fastapi import Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shortener_app.security.auth.errors import AuthError
from shortener_app.security.auth.model import IssuedJWTToken
from shortener_app.security.auth.dto import TokensDTO, UserCredentialsDTO
from shortener_app.security.utils import get_sha256_hash
from shortener_app.database.models import APIUser
from .middleware.jwt.base.auth import JWTAuth
from .middleware.jwt.base.token_types import TokenType
from .middleware.jwt.errors import AccessError
from .middleware.jwt.utils import check_revoked, generate_device_id, try_decode_token
from .errors import ErrorObj


class AuthService:
    def __init__(self, jwt_auth: JWTAuth) -> None:
        self._jwt_auth = jwt_auth

    async def register(
            self, 
            body: UserCredentialsDTO, 
            session: AsyncSession
        ) -> tuple[TokensDTO, None] | tuple[None, ErrorObj]:
        result = await (
            session
            .execute(
                select(APIUser)
                .where(APIUser.email == body.email)
            )
        )
        if result.scalar_one_or_none():
            return None, AuthError.get_email_occupied_error()

        user = APIUser(
            email=body.email, 
            password_hash=get_sha256_hash(line=body.password)
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        access_token, refresh_token = await self._issue_tokens_for_user(user=user, session=session)

        return TokensDTO(access_token=access_token, refresh_token=refresh_token), None

    async def login(
            self, 
            body: UserCredentialsDTO, 
            session: AsyncSession
        ) -> tuple[TokensDTO, None] | tuple[None, ErrorObj]:
        result = await (
            session
            .execute(
                select(APIUser)
                .where(
                    APIUser.email == body.email, 
                    APIUser.password_hash == get_sha256_hash(line=body.password)
                )
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None, AuthError.get_invalid_credentials_error()

        access_token, refresh_token = await self._issue_tokens_for_user(user=user, session=session)

        return TokensDTO(access_token=access_token, refresh_token=refresh_token), None

    async def logout(
            self, 
            user: APIUser, 
            device_id: str, 
            session: AsyncSession
        ) -> None:
        await (
            session
            .execute(
                update(IssuedJWTToken)
                .where(
                    IssuedJWTToken.subject_id == user.id, 
                    IssuedJWTToken.device_id == device_id)
                .values(revoked = True)
            )
        )
        await session.commit()
        # await user.tokens.filter(device_id=device_id).update(revoked=True)

    async def update_tokens(
        self, 
        # user: APIUser,
        request: Request,
        refresh_token: str, 
        session: AsyncSession,
    ) -> tuple[TokensDTO, None] | tuple[None, ErrorObj]:
        payload, error = try_decode_token(jwt_auth=self._jwt_auth, token=refresh_token)

        if error:
            return None, AccessError.get_invalid_token_error()

        if payload['type'] != TokenType.REFRESH.value:
            return None, AccessError.get_incorrect_token_type_error()
        
        result = await (
            session
            .execute(
                select(APIUser)
                .where(APIUser.id==payload["sub"])
            )
        )
        user = result.scalar_one_or_none()

        if user is None:
            return None, AccessError.get_incorrect_token_type_error()
        # Если обновленный токен пробуют обновить ещё раз,
        # нужно отменить все выущенные на пользователя токены и вернуть ошибку
        if await check_revoked(payload['jti'], session=session):
            await (
                session
                .execute(
                    update(IssuedJWTToken)
                    .where(IssuedJWTToken.subject_id == user.id)
                    .values(revoked = True)
                )
            )
            await session.commit()
            return None, AccessError.get_token_already_revoked_error()

        device_id = payload['device_id']
        await (
            session
            .execute(
                update(IssuedJWTToken)
                .where(
                    IssuedJWTToken.subject_id == user.id, 
                    IssuedJWTToken.device_id == device_id)
                .values(revoked = True)
            )
        )
        access_token, refresh_token = await self._issue_tokens_for_user(user=user, session=session, device_id=device_id)
        request.state.user = user

        return TokensDTO(access_token=access_token, refresh_token=refresh_token), None

    async def _issue_tokens_for_user(
            self, 
            user: APIUser, 
            session: AsyncSession,
            device_id: str = generate_device_id(),
        ) -> tuple[str, str]:
        access_token = self._jwt_auth.generate_access_token(subject=str(user.id), payload={'device_id': device_id})
        refresh_token = self._jwt_auth.generate_refresh_token(subject=str(user.id), payload={'device_id': device_id})

        raw_tokens = [self._jwt_auth.get_raw_jwt(token) for token in [access_token, refresh_token]]
        new_tokens = [
                IssuedJWTToken(
                    subject_id=user.id,
                    jti=token_payload['jti'],
                    device_id=device_id,
                    # expired_time=token_payload['exp']
                )
                for token_payload in raw_tokens
            ]
        session.add_all(new_tokens)
        await session.commit()
        

        return access_token, refresh_token