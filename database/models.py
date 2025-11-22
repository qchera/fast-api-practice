import uuid
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import Column, DateTime
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
    estimated_delivery: datetime = Field(sa_column=Column(
                                             DateTime(timezone=True),
                                             nullable=False
                                         ))

    buyer_id: UUID = Field(foreign_key="user.id", nullable=False)
    buyer: "User" = Relationship(
        back_populates="purchases",
        sa_relationship_kwargs={
            "foreign_keys": "[Shipment.buyer_id]",
            "lazy": "selectin"
        }
    )

    seller_id: UUID = Field(foreign_key="user.id", nullable=False)
    seller: "User" = Relationship(
        back_populates="sales",
        sa_relationship_kwargs={
            "foreign_keys": "[Shipment.seller_id]",
            "lazy": "selectin"
        }
    )

    @property
    def buyer_username(self) -> str | None:
        return self.buyer.username if self.buyer else None

    @property
    def seller_username(self) -> str | None:
        return self.seller.username if self.seller else None

class ShipmentCreate(SQLModel):
    product: str = Field(nullable=False)
    progress: ProgressStatus = Field(default=ProgressStatus.PLACED)
    estimated_delivery: datetime | None = Field(default_factory=lambda: datetime.now() + timedelta(days=7))

    buyer_id: UUID = Field(default=None)
    seller_id: UUID = Field(default=None)

class ShipmentCreateSimple(SQLModel):
    product: str = Field(nullable=False)
    progress: ProgressStatus = Field(default=ProgressStatus.PLACED)
    estimated_delivery: datetime | None = Field(default_factory=lambda: datetime.now() + timedelta(days=7))

    buyer_username: str = Field(nullable=False)

class ShipmentSummary(SQLModel):
    product: str | None = Field(default=None)
    progress: ProgressStatus | None = Field(default=None)
    estimated_delivery: datetime | None = Field(default=None)

    buyer_username: str = Field(nullable=False)
    seller_username: str = Field(nullable=False)

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

    purchases: list["Shipment"] = Relationship(
        back_populates="buyer",
        sa_relationship_kwargs={
            "primaryjoin": "User.id==Shipment.buyer_id",
            "lazy": "selectin"
        }
    )

    sales: list["Shipment"] = Relationship(
        back_populates="seller",
        sa_relationship_kwargs={
            "primaryjoin": "User.id==Shipment.seller_id",
            "lazy": "selectin"
        }
    )

class UserCreate(SQLModel):
    username: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    email: EmailStr = Field(nullable=False)
    password: str = Field(nullable=False)

class UserPlain(SQLModel):
    username: str
    full_name: str
    email: EmailStr

class UserRead(SQLModel):
    id: UUID
    username: str
    full_name: str
    email: EmailStr

    purchases: list[ShipmentSummary]
    sales: list[ShipmentSummary]

class ShipmentRead(SQLModel):
    id: UUID
    product: str
    progress: ProgressStatus
    estimated_delivery: datetime

    buyer: UserPlain | None = None
    seller: UserPlain | None = None