import uuid
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import Column
from sqlalchemy.dialects import postgresql
from sqlmodel import Relationship
from sqlmodel import SQLModel, Field

class ProgressStatus(str, Enum):
    PLACED = "placed"
    IN_TRANSIT = "in transit"
    SHIPPED = "shipped"

class Shipment(SQLModel, table=True):
    __tablename__ = "shipment"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        )
    )
    product: str = Field(nullable=False)
    progress: ProgressStatus = Field(nullable=False)
    estimated_delivery: datetime = Field(nullable=False)

    user_id: UUID = Field(foreign_key="user.id", nullable=False)
    user: "User" = Relationship(
        back_populates="shipments",
        sa_relationship_kwargs={"lazy": "joined"}
    )

class ShipmentCreate(SQLModel):
    product: str = Field(nullable=False)
    progress: ProgressStatus = Field(default=ProgressStatus.PLACED)
    estimated_delivery: datetime = Field(default_factory=lambda: datetime.now() + timedelta(days=7))

    user_id: UUID = Field(default=None)

class ShipmentUpdate(SQLModel):
    product: str | None = Field(default=None)
    progress: ProgressStatus | None = Field(default=None)
    estimated_delivery: datetime | None = Field(default=None)

class User(SQLModel,  table=True):
    __tablename__ = "user"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        )
    )
    username: str = Field(nullable=False, unique=True)
    full_name: str = Field(nullable=False)
    email: EmailStr = Field(nullable=False, unique=True)
    hashed_password: str = Field(nullable=False)

    shipments: list[Shipment] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"lazy": "selectin"}
    )

class UserCreate(SQLModel):
    username: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    email: EmailStr = Field(nullable=False)
    password: str = Field(nullable=False)

class UserRead(SQLModel):
    username: str
    full_name: str
    email: EmailStr