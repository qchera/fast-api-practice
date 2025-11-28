import json
import uuid
from datetime import timedelta, datetime, timezone

from fastapi import HTTPException, status

import jwt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from ..config import security_settings


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def generate_url_safe_token(data: dict) -> str:
    return _serializer.dumps(data)

def decode_url_safe_token(token: str, expiry: timedelta | None = None) -> dict | None:
    try:
        token_data: dict = _serializer.loads(token,
                                             max_age=int(expiry.total_seconds()) if expiry else None)
        return token_data
    except SignatureExpired as e:
        expired_data: dict = _serializer.load_payload(e.payload)
        print(expired_data)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "Token has expired", "userId": expired_data.get('id')}
        )
    except BadSignature:
        print('Token invalid')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception:
        return None
