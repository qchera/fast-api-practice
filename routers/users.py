from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from starlette.websockets import WebSocket, WebSocketDisconnect

from ..core.security import oauth2_scheme
from ..database.schemas.user import UserCreate, UserRead
from ..dependencies import UserServiceDep, get_access_token_data, get_redis_auth_service
from ..services.redis_auth_service import RedisAuthService
from ..utils.socket_manager import socket_manager
from ..utils.utils import decode_access_token

router = APIRouter(tags=["Users"])

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, users_service: UserServiceDep) -> None:
    await users_service.register_user(user_data)


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], users_service: UserServiceDep
) -> str:
    return await users_service.token(form_data.username, form_data.password)


@router.get("/decode")
async def decode_token(token: Annotated[str, Depends(oauth2_scheme)], users_service: UserServiceDep) -> UserRead:
    data = decode_access_token(token)
    if data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await users_service.find_by_id(data["user"]["id"])
    user_read = UserRead.model_validate(user)
    return user_read


@router.get("/logout")
async def logout(
    token_data: Annotated[dict, Depends(get_access_token_data)],
    redis_auth_service: Annotated[RedisAuthService, Depends(get_redis_auth_service)],
):
    await redis_auth_service.revoke_token(token_data)


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: UUID):
    await socket_manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket, user_id)
