from uuid import UUID

from redis import asyncio as aioredis
from fastapi import HTTPException, status
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional

from .services.redis_auth_service import RedisAuthService
from .core import redis
from .database.models import User, UserRead
from .utils import decode_access_token
from .core.security import oauth2_scheme
from .database.session import get_session
from .services.shipments_service import ShipmentService
from .services.users_service import UserService

SessionDep = Annotated[AsyncSession, Depends(get_session)]

def get_redis_client() -> aioredis.Redis:
    if redis.redis_client is None:
        raise RuntimeError('Redis client not set')
    return redis.redis_client

def get_redis_auth_service(redis_client: Annotated[aioredis.Redis, Depends(get_redis_client)]) -> RedisAuthService:
    return RedisAuthService(redis_client)

RedisAuthServiceDep = Annotated[RedisAuthService, Depends(get_redis_auth_service)]

async def get_access_token_data(token: Annotated[str, Depends(oauth2_scheme)],
                          redis_client: RedisAuthServiceDep) -> dict:
    data: dict = decode_access_token(token)
    if await redis_client.token_blacklisted(data["jti"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token has been revoked"
        )
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return data

async def get_logged_in_user(token_data: Annotated[dict, Depends(get_access_token_data)],
                             session: SessionDep) -> User:
    user: Optional[User] = await session.get(User, UUID(token_data["user"]["id"]))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authenticated user found"
        )
    return user

def get_shipment_service(session: SessionDep) -> ShipmentService:
    return ShipmentService(session)

def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)

ShipmentServiceDep = Annotated[ShipmentService, Depends(get_shipment_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
UserDep = Annotated[UserRead, Depends(get_logged_in_user)]
