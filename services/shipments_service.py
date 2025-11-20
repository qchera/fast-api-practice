from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Shipment, ProgressStatus, ShipmentCreate, ShipmentUpdate

class ShipmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_shipments(self) -> list[Shipment]:
        result = await self.session.execute(select(Shipment))
        shipments = result.scalars().all()
        if not shipments:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no shipments found")
        return list(shipments)

    async def get_shipment_by_id(self, shipment_id: UUID) -> Shipment:
        shipment: Shipment | None = await self.session.get(Shipment, shipment_id)
        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shipment id {shipment_id} does not exist")
        return shipment

    async def get_shipments_by_user_id(self, user_id):
        shipments = await self.session.execute(select(Shipment).where(Shipment.user_id == user_id))
        shipments_list = shipments.scalars().all()
        return list(shipments_list)

    async def fill_table(self, user_id: UUID) -> None:
        items = [
            ("Apple iPhone 13", ProgressStatus.PLACED),
            ("Samsung Galaxy S21", ProgressStatus.IN_TRANSIT),
            ("Canon EOS 5D Mark IV", ProgressStatus.SHIPPED),
            ("Microsoft Xbox Series X", ProgressStatus.IN_TRANSIT),
            ("DJI Mavic Air 2 Drone", ProgressStatus.SHIPPED),
            ("ASUS ROG Zephyrus G14 laptop", ProgressStatus.PLACED),
            ("Nintendo Switch OLED Model", ProgressStatus.IN_TRANSIT),
            ("Google Pixel 6 Pro", ProgressStatus.SHIPPED),
            ("Bose QuietComfort 45 Headphones", ProgressStatus.PLACED),
            ("Sony PlayStation 5", ProgressStatus.IN_TRANSIT),
            ("Apple AirPods Pro 2", ProgressStatus.SHIPPED),
            ("Samsung Odyssey G9 Gaming Monitor", ProgressStatus.PLACED),
            ("ASUS RT-AC68U Wi-Fi Router", ProgressStatus.IN_TRANSIT),
            ("Logitech G502 Gaming Mouse", ProgressStatus.SHIPPED),
            ("Nintendo Switch Pro Controller", ProgressStatus.PLACED),
        ]

        for product, progress in items:
            shipment_create = ShipmentCreate(product=product, progress=progress, user_id=user_id)
            shipment = Shipment.model_validate(shipment_create)
            self.session.add(shipment)

        await self.session.commit()

    async def create_shipment(self, shipment_data: ShipmentCreate, user_id: UUID) -> Shipment:
        shipment_data.user_id = user_id
        shipment = Shipment.model_validate(shipment_data)
        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment

    async def update_shipment(
        self, shipment_id: UUID, shipment_update: ShipmentUpdate
    ) -> Shipment:
        update_data = shipment_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shipment data is invalid or empty"
            )

        shipment = await self.get_shipment_by_id(shipment_id)

        shipment.sqlmodel_update(update_data)
        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment

    async def delete_shipment(self, shipment_id: UUID) -> None:
        shipment = await self.get_shipment_by_id(shipment_id)
        await self.session.delete(shipment)
        await self.session.commit()
