import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects import postgresql
from sqlmodel import Field, Relationship, SQLModel

from .enums import ProgressStatus, ApprovalStatus

if TYPE_CHECKING:
    from .user import User

class Shipment(SQLModel, table=True):
    __tablename__ = "shipment"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(postgresql.UUID(as_uuid=True), primary_key=True)
    )
    product: str = Field(nullable=False)
    progress: ProgressStatus = Field(nullable=False, default=ProgressStatus.PLACED)
    estimated_delivery: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    approval_status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)

    buyer_id: UUID = Field(foreign_key="user.id", nullable=False)
    seller_id: UUID = Field(foreign_key="user.id", nullable=False)

    buyer: "User" = Relationship(
        back_populates="purchases",
        sa_relationship_kwargs={
            "foreign_keys": "[Shipment.buyer_id]",
            "lazy": "selectin"
        }
    )

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