from uuid import UUID
from pydantic import EmailStr

from .common import CamelModel
from .shipment import ShipmentSummary

class UserBase(CamelModel):
    username: str
    full_name: str
    email: EmailStr

class UserPlain(UserBase):
    id: UUID

class UserCreate(UserBase):
    password: str

class UserRead(UserPlain):
    purchases: list[ShipmentSummary] = []
    sales: list[ShipmentSummary] = []