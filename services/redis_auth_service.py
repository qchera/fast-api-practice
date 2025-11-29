from datetime import datetime, timezone
import jwt
from fastapi import status
from redis import asyncio as aioredis
from ..utils.exceptions import AppException
from ..utils.errors import ErrorCode

class RedisAuthService:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def token_blacklisted(self, token_jti: str) -> bool:
        return await self.redis.get(token_jti) is not None

    async def revoke_token(self ,token_data: dict):
        try:
            expiry_timestamp = token_data.get("exp")
            if expiry_timestamp is None:
                raise AppException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    code=ErrorCode.TOKEN_MISSING_EXP,
                    message="Token does not have an expiry"
                )
            expiry_datetime = datetime.fromtimestamp(expiry_timestamp, tz=timezone.utc)
            now_datetime = datetime.now(timezone.utc)
            expiry_seconds = int((expiry_datetime - now_datetime).total_seconds())
            if expiry_seconds > 0:
                await self.redis.setex(token_data["jti"], expiry_seconds, "revoked")
        except jwt.PyJWTError:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code=ErrorCode.TOKEN_REVOKE_FAILED,
                message="Impossible to revoke token"
            )