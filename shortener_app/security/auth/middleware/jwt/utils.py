import uuid
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base.auth import JWTAuth
from shortener_app.security.auth.model import IssuedJWTToken


def generate_device_id() -> str:
    return str(uuid.uuid4())


async def check_revoked(jti: str, session: AsyncSession) -> bool:
    result = await (
        session
        .execute(
            select(IssuedJWTToken)
            .where(IssuedJWTToken.jti==jti, IssuedJWTToken.revoked==True)
        )
    )
    return result.scalar_one_or_none()
    # return await IssuedJWTToken.filter(jti=jti, revoked=True).exists()


def try_decode_token(jwt_auth: JWTAuth, token: str) -> tuple[dict, None] | tuple[None, InvalidTokenError]:
    try:
        payload = jwt_auth.verify_token(token)
        return payload, None
    except InvalidTokenError as error:
        return None, error