from typing import Annotated, Any, Coroutine

from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from ..services.redis_auth_service import RedisAuthService
from ..core.security import oauth2_scheme
from ..utils import decode_access_token
from ..database.models import UserCreate, UserRead
from ..dependencies import UserServiceDep, get_access_token_data, get_redis_auth_service

router = APIRouter(tags=["Users"])

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, users_service: UserServiceDep):
    await users_service.register_user(user_data)

@router.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], users_service: UserServiceDep):
    return await users_service.token(form_data.username, form_data.password)

@router.get("/decode")
async def decode_token(token: Annotated[str, Depends(oauth2_scheme)], users_service: UserServiceDep) -> UserRead:
    data = decode_access_token(token)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    user = await users_service.find_by_id(data["user"]["id"])
    user_read = UserRead.model_validate(user)
    return user_read

@router.get("/logout")
async def logout(token_data: Annotated[dict, Depends(get_access_token_data)], redis_auth_service: Annotated[RedisAuthService, Depends(get_redis_auth_service)]):
    await redis_auth_service.revoke_token(token_data)