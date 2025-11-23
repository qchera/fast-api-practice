import uuid
from datetime import timedelta, datetime, timezone

from fastapi import HTTPException, status

import jwt

from ..config import security_settings


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
