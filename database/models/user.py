import uuid
from typing import TYPE_CHECKING, List
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import Column
from sqlalchemy.dialects import postgresql
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .shipment import Shipment

class User(SQLModel, table=True):
    __tablename__ = "user"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(postgresql.UUID(as_uuid=True), primary_key=True)
    )
    username: str = Field(nullable=False, unique=True, index=True)
    full_name: str = Field(nullable=False)
    email: EmailStr = Field(nullable=False, unique=True, index=True)
    email_verified: bool = Field(nullable=False, default=False)
    hashed_password: str = Field(nullable=False)

    purchases: List["Shipment"] = Relationship(
        back_populates="buyer",
        sa_relationship_kwargs={
            "primaryjoin": "User.id==Shipment.buyer_id",
            "lazy": "selectin"
        }
    )

    sales: List["Shipment"] = Relationship(
        back_populates="seller",
        sa_relationship_kwargs={
            "primaryjoin": "User.id==Shipment.seller_id",
            "lazy": "selectin"
        }
    )