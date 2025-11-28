from typing import Any
from uuid import UUID

from asyncpg.pgproto.pgproto import timedelta
from passlib.context import CryptContext
from fastapi import status, HTTPException, BackgroundTasks, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, Select
from sqlalchemy.orm import selectinload

from ..utils.utils import decode_url_safe_token
from ..utils.utils import generate_url_safe_token
from .email_service import EmailService
from ..utils.utils import generate_access_token
from ..database.models.user import User
from ..database.models.shipment import Shipment
from ..database.schemas.user import UserCreate, UserBase, UserPlain


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return password_context.encrypt(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_context.verify(password, hashed_password)

class UserService():
    def __init__(self, session: AsyncSession, email_service: EmailService, background_tasks: BackgroundTasks):
        self.session = session
        self.email_service = email_service
        self.background_tasks = background_tasks

    async def register_user(self, user_data: UserCreate) -> str:
        user: User = User(
            **user_data.model_dump(exclude={"password"})
        )
        find_by_email: Select[Any] = select(User).where(User.email == user.email)
        find_by_username: Select[Any] = select(User).where(User.username == user.username)
        if (await self.session.execute(find_by_email)).scalars().one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        if (await self.session.execute(find_by_username)).scalars().one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        user.hashed_password = hash_password(user_data.password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        self._send_email_verification(UserPlain(**user.model_dump()))

        return str(user.id)

    async def token(self, login, password) -> str:
        find_by_email_or_username = select(User).where(or_(User.email == login, User.username == login))
        user = (await self.session.execute(find_by_email_or_username)).scalars().one_or_none()
        print(user, login)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wrong credentials"
            )
        if not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verify your email before logging in"
            )
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incorrect password"
            )

        token = generate_access_token(
            data={
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                }
            },
            #expiry=timedelta(seconds=15)
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def find_by_username(self, username: str) -> User:
        find_by_email = select(User).where(User.username == username)
        user = (await self.session.execute(find_by_email)).scalars().one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def verify_url_safe_token(self, token: str) -> None:
        token_data = decode_url_safe_token(token, timedelta(hours=24))
        if token_data is None:
            print('Token data is None')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate token",
            )
        user: User | None = await self.session.get(User, token_data["id"])
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Something went wrong, please try to register again"
            )
        if user.email == token_data["email"] and not user.email_verified:
            user.email_verified = True
            self.session.add(user)
            await self.session.commit()

    async def resend_email_verification(self, user_id: UUID) -> None:
        user: User | None = await self.session.get(User, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Something went wrong, please try to register again"
            )
        self._send_email_verification(UserPlain(**user.model_dump()))


    def _send_email_verification(self, user: UserPlain):
        token = generate_url_safe_token({
            "email": user.email,
            "id": str(user.id),
        })
        self.background_tasks.add_task(
            self.email_service.send_verification_email,
            UserBase(**user.model_dump()),
            token)
