from datetime import timedelta
from typing import Any
from uuid import UUID

from itsdangerous import SignatureExpired
from passlib.context import CryptContext
from fastapi import status, BackgroundTasks
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, Select
from sqlalchemy.orm import selectinload

from ..celery_module.worker import send_verification_email_task
from ..celery_module.worker import send_password_reset_email_task
from ..utils.utils import decode_url_safe_token, generate_url_safe_token, generate_access_token
from .email_service import EmailService
from ..database.models.user import User
from ..database.models.shipment import Shipment
from ..database.schemas.user import UserCreate, UserBase, UserPlain
from ..utils.exceptions import AppException
from ..utils.errors import ErrorCode

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.encrypt(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_context.verify(password, hashed_password)


async def get_one_or_none(select: Select, session: AsyncSession):
    result = await session.execute(select)
    return result.scalars().one_or_none()


class UserService():
    def __init__(self, session: AsyncSession, email_service: EmailService, background_tasks: BackgroundTasks):
        self.session = session
        self.email_service = email_service
        self.background_tasks = background_tasks

    async def register_user(self, user_data: UserCreate) -> str:
        user: User = User(
            **user_data.model_dump(exclude={"new_password"})
        )
        find_by_email: Select[Any] = select(User).where(User.email == user.email)
        find_by_username: Select[Any] = select(User).where(User.username == user.username)

        if await get_one_or_none(find_by_email, self.session) is not None:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code=ErrorCode.EMAIL_TAKEN,
                message="Email already registered"
            )
        if await get_one_or_none(find_by_username, self.session) is not None:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code=ErrorCode.USERNAME_TAKEN,
                message="Username already taken"
            )

        user.hashed_password = hash_password(user_data.password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        self._send_email_verification(UserPlain(**user.model_dump()))

        return str(user.id)

    async def token(self, login, password) -> str:
        find_by_email_or_username = select(User).where(or_(User.email == login, User.username == login))
        user = await get_one_or_none(find_by_email_or_username, self.session)
        print(user, login)

        if user is None:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.WRONG_LOGIN,
                message="No user associated with given email or username"
            )

        if not user.email_verified:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code=ErrorCode.EMAIL_NOT_VERIFIED,
                message="Verify your email before logging in",
                meta={"email": user.email}
            )

        if not verify_password(password, user.hashed_password):
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.WRONG_PASSWORD,
                message="Wrong password",
                meta={"email": user.email}
            )

        token = generate_access_token(
            data={
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                }
            },
        )

        return token

    async def find_by_id(self, id: UUID) -> User:
        query = select(User).where(User.id == id).options(
            selectinload(User.purchases).selectinload(Shipment.seller),
            selectinload(User.sales).selectinload(Shipment.buyer)
        )

        result = await self.session.execute(query)
        user = result.scalars().one_or_none()

        if user is None:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.USER_NOT_FOUND,
                message="User not found"
            )
        return user

    async def find_by_username(self, username: str) -> User:
        find_by_username = select(User).where(User.username == username)
        user = await get_one_or_none(find_by_username, self.session)
        if user is None:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.USER_NOT_FOUND,
                message="User not found"
            )
        return user

    async def find_by_email(self, email: str) -> User:
        find_by_email = select(User).where(User.email == email)
        user = await get_one_or_none(find_by_email, self.session)
        if user is None:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.USER_NOT_FOUND,
                message="User not found"
            )
        return user

    async def verify_url_safe_token(self, token: str) -> None:
        user: User | None = None
        token_data: dict | None = None
        try:
            token_data = decode_url_safe_token(token, timedelta(hours=24))

            if token_data is None:
                raise AppException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.TOKEN_INVALID,
                    message="Could not validate token"
                )
        except AppException as e:
            if (e.detail.get('code') == ErrorCode.TOKEN_EXPIRED
                    and e.detail.get('meta')
                    and e.detail.get('meta').get('user_id')
                    and e.detail.get('meta').get('email')):
                user_id = e.detail.get('meta').get('user_id')
                user_email = e.detail.get('meta').get('email')

                if not user_id:
                    raise AppException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        code=ErrorCode.TOKEN_INVALID,
                        message="Could not validate token"
                    )

                user = await self.session.get(User, user_id)
                if user is None or user.email != user_email:
                    raise AppException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        code=ErrorCode.USER_NOT_FOUND,
                        message="Something went wrong, please try to register again"
                    )

                if user.email_verified:
                    return None
                raise e
            else:
                raise e

        if user is None:
            user = await self.find_by_id(token_data['id'])

        if user.email == token_data['email'] and not user.email_verified:
            user.email_verified = True
            self.session.add(user)
            await self.session.commit()
        return None

    async def resend_email_verification(self,
                                        *,
                                        token: str | None = None,
                                        email: EmailStr | None = None) -> None:
        target_email: str | None = email

        if token:
            payload = decode_url_safe_token(token)
            if payload:
                target_email = payload.get("email")

        if not target_email:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.USER_NOT_FOUND,
                message="Something went wrong, please try to register again"
            )
        user: User | None = await self.find_by_email(target_email)
        if user is None:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.USER_NOT_FOUND,
                message="Something went wrong, please try to register again"
            )
        if user.email_verified:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code=ErrorCode.EMAIL_ALREADY_VERIFIED,
                message="Email already verified"
            )
        self._send_email_verification(UserPlain(**user.model_dump()))

    async def send_password_reset(self, *, email: EmailStr) -> None:
        user: User | None = await self.find_by_email(email)
        token = generate_url_safe_token({
            'email': user.email,
        }, salt="password-reset-token")
        send_password_reset_email_task.delay(
            user.model_dump(),
            token
        )

    async def reset_password(self, *, token: str, new_pass: str) -> None:
        data: dict | None = decode_url_safe_token(token, timedelta(minutes=10), salt="password-reset-token")
        user: User = await self.find_by_email(data['email'])
        user.hashed_password = hash_password(new_pass)
        self.session.add(user)
        await self.session.commit()

    def _send_email_verification(self, user: UserPlain):
        token = generate_url_safe_token({
            "email": user.email,
            "id": str(user.id),
        })
        send_verification_email_task.delay(
            user.model_dump(),
            token
        )