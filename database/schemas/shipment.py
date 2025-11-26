from datetime import datetime, timedelta
from uuid import UUID

from sqlmodel import Field

from ..models.enums import ProgressStatus, ApprovalStatus
from .common import CamelModel

class ShipmentBase(CamelModel):
    product: str
    progress: ProgressStatus = ProgressStatus.PLACED
    estimated_delivery: datetime | None = Field(
        default_factory=lambda: datetime.now() + timedelta(days=7)
    )
    approval_status: ApprovalStatus = ApprovalStatus.PENDING

class ShipmentCreate(ShipmentBase):
    buyer_id: UUID | None = None
    seller_id: UUID | None = None

class ShipmentCreateSimple(ShipmentBase):
    buyer_username: str

class ShipmentSummary(CamelModel):
    id: UUID
    product: str
    progress: ProgressStatus
    estimated_delivery: datetime
    approval_status: ApprovalStatus
    buyer_username: str
    seller_username: str

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..schemas.user import UserPlain

class ShipmentRead(ShipmentBase):
    id: UUID
    buyer: "UserPlain | None" = None
    seller: "UserPlain | None" = None

class ShipmentStatusUpdate(CamelModel):
    approval_status: ApprovalStatus