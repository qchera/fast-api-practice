from datetime import timedelta
from typing import Optional
from uuid import UUID

from passlib.context import CryptContext
from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..utils import generate_access_token
from ..database.models import UserCreate, User, UserRead


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return password_context.encrypt(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_context.verify(password, hashed_password)

class UserService():
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(self, user_data: UserCreate) -> str:
        user: User = User(
            **user_data.model_dump(exclude={"password"})
        )
        find_by_email = select(User).where(User.email == user.email)
        find_by_username = select(User).where(User.username == user.username)
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
        return str(user.id)

    async def token(self, email, password) -> str:
        find_by_email = select(User).where(User.email == email)
        user = (await self.session.execute(find_by_email)).scalars().one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )

        token = generate_access_token(
            data={
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "full_name": user.full_name,
                }
            },
            #expiry=timedelta(seconds=15)
        )

        return token

    async def find_by_id(self, id: UUID) -> User:
        user: User | None = await self.session.get(User, id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
