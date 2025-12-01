from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from starlette.websockets import WebSocket, WebSocketDisconnect

from ..database.schemas.common import PasswordResetModel
from ..services.socket_message_service import socket_message_service
from ..core.security import oauth2_scheme
from ..database.schemas.user import UserCreate, UserRead
from ..dependencies import UserServiceDep, get_access_token_data, get_redis_auth_service
from ..services.redis_auth_service import RedisAuthService
from ..utils.socket_manager import socket_manager
from ..utils.utils import decode_access_token
from ..utils.exceptions import AppException
from ..utils.errors import ErrorCode

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
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.TOKEN_INVALID,
            message="Invalid token"
        )
    user = await users_service.find_by_id(data["user"]["id"])
    user_read = UserRead.model_validate(user)
    return user_read


@router.get("/logout")
async def logout(
    token_data: Annotated[dict, Depends(get_access_token_data)],
    redis_auth_service: Annotated[RedisAuthService, Depends(get_redis_auth_service)],
) -> None:
    await redis_auth_service.revoke_token(token_data)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str) -> None:
    user_id: UUID
    try:
        payload = decode_access_token(token)
        user_id = UUID(payload["user"]["id"])
    except Exception as e:
        print("WS Auth error", e)
        await websocket.close(1008)
        return
    await socket_manager.connect(websocket, user_id)
    try:
        while True:
            text: str = await websocket.receive_text()
            if text == 'PING':
                print(text)
                await socket_message_service.heartbeat(user_id)
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket, user_id)

@router.post("/verify-email")
async def verify_email(token: str, users_service: UserServiceDep) -> None:
    await users_service.verify_url_safe_token(token)


@router.post("/resend-verification")
async def resend_email_verification(token: str, user_service: UserServiceDep) -> None:
    await user_service.resend_email_verification(token=token)


@router.post("/resend-verification-by-email")
async def resend_email_verification(user_service: UserServiceDep, email: EmailStr = Body(embed=True)) -> None:
    await user_service.resend_email_verification(email=email)


@router.post("/request-reset-password")
async def request_reset_password(user_service: UserServiceDep, email: EmailStr = Body(embed=True)) -> None:
    await user_service.send_password_reset(email=email)

@router.post("/reset-password")
async def reset_password(user_service: UserServiceDep, password_reset: PasswordResetModel) -> None:
    await user_service.reset_password(token=password_reset.token, new_pass=password_reset.new_password)
