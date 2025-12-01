import uuid
from datetime import timedelta, datetime, timezone

from fastapi import status

import jwt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from ..config import security_settings
from .exceptions import AppException
from .errors import ErrorCode


_serializer = URLSafeTimedSerializer(security_settings.JWT_SECRET)

def generate_access_token(
        data: dict,
        expiry: timedelta = timedelta(minutes=15),
) -> str:
    jti = str(uuid.uuid4())
    return jwt.encode(
        payload={
            **data,
            "jti": jti,
            "exp": datetime.now(timezone.utc) + expiry
        },
        algorithm=security_settings.JWT_ALGORITHM,
        key=security_settings.JWT_SECRET
    )

def decode_access_token(token: str) -> dict:
    try:
        token_data: dict = jwt.decode(
            jwt=token,
            key=security_settings.JWT_SECRET,
            algorithms=[security_settings.JWT_ALGORITHM]
        )
        return token_data
    except jwt.ExpiredSignatureError:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.ACCESS_TOKEN_EXPIRED,
            message="Token has expired"
        )
    except jwt.PyJWTError:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.ACCESS_TOKEN_INVALID,
            message="Invalid token"
        )

def generate_url_safe_token(data: dict, salt: str | None = None) -> str:
    return _serializer.dumps(data, salt=salt)

def decode_url_safe_token(token: str, expiry: timedelta | None = None, salt: str | None = None) -> dict | None:
    try:
        token_data: dict = _serializer.loads(token,
                                             max_age=int(expiry.total_seconds()) if expiry else None,
                                             salt=salt)
        return token_data
    except SignatureExpired as e:
        expired_data: dict = _serializer.load_payload(e.payload)
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.TOKEN_EXPIRED,
            message="Token has expired",
            meta={"user_id": expired_data.get('id'), "email": expired_data.get('email')}
        )
    except BadSignature:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.TOKEN_INVALID,
            message="Invalid token"
        )
    except Exception:
        return None