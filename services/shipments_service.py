from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import HTTPException, status, BackgroundTasks
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.schemas.user import UserBase
from .email_service import EmailService
from .socket_message_service import SocketMessageService
from ..database.schemas.shipment import ProgressStatus, ShipmentCreate, ShipmentSummary, ApprovalStatus, ShipmentCreateSimple
from ..database.models.shipment import Shipment
from ..database.models.user import User

class ShipmentService:
    def __init__(self, session: AsyncSession, socket_service: SocketMessageService, email_service: EmailService, background_tasks: BackgroundTasks):
        self.session = session
        self.socket_service = socket_service
        self.email_service = email_service
        self.background_tasks = background_tasks

    async def get_all_shipments(self) -> list[ShipmentSummary]:
        result = await self.session.execute(select(Shipment))
        shipments = result.scalars().all()
        if not shipments:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no shipments found")
        return [ShipmentSummary.model_validate(shipment) for shipment in shipments]

    async def get_shipment_by_id(self, shipment_id: UUID) -> Shipment:
        shipment: Shipment | None = await self.session.get(Shipment, shipment_id)
        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shipment id {shipment_id} does not exist")
        return shipment

    async def get_shipments_by_user_id(self, user_id) -> List[Shipment]:
        shipments = await self.session.execute(select(Shipment).where(Shipment.user_id == user_id))
        shipments_list = shipments.scalars().all()
        return list(shipments_list)

    async def create_shipment(self, shipment_data_simple: ShipmentCreateSimple,
                              user_id: UUID) -> ShipmentSummary:
        shipment_data: ShipmentCreate = await self.map_simple_to_create(shipment_data_simple, user_id)
        shipment_data_valid = self._validate_shipment_create(shipment_data)
        clean_data = shipment_data_valid.model_dump()
        shipment = Shipment.model_validate(clean_data)
        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        shipment_summary: ShipmentSummary = ShipmentSummary.model_validate(shipment)
        await self.socket_service.add_pending_purchase_message(shipment.buyer_id, shipment_summary)
        self.background_tasks.add_task(
            self.email_service.send_shipment_created,
            shipment_summary,
            UserBase(**shipment.seller.model_dump()),
            UserBase(**shipment.buyer.model_dump())
        )
        return shipment_summary

    async def delete_shipment(self, shipment_id: UUID) -> None:
        shipment = await self.get_shipment_by_id(shipment_id)
        await self.session.delete(shipment)
        await self.session.commit()

    '''
        async def update_shipment(
            self, shipment_id: UUID, shipment_update: ShipmentSummary
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
    '''

    async def update_shipment_approval_status(self,
                                              shipment_id: UUID,
                                              approval_status: ApprovalStatus) -> ShipmentSummary:
        if approval_status == ApprovalStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update approval status to 'pending'"
            )
        shipment: Shipment | None = await self.session.get(Shipment, shipment_id)

        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment with id '{shipment_id}' not found"
            )

        shipment.approval_status = approval_status
        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        shipment_summary: ShipmentSummary = ShipmentSummary.model_validate(shipment)
        await self.socket_service.update_sale_message(shipment.seller_id, shipment_summary)
        self.background_tasks.add_task(
            self.email_service.send_modified_approval,
            shipment_summary,
            UserBase(**shipment.seller.model_dump()),
            UserBase(**shipment.buyer.model_dump())
        )
        return shipment_summary

    def _validate_shipment_create(self, shipment_data: ShipmentCreate) -> ShipmentCreate:
        valid_shipment = shipment_data.model_dump(exclude_none=True)
        delivery_progress: str = valid_shipment.get("progress")
        estimated_delivery = valid_shipment.get("estimated_delivery")
        current_time = datetime.now(timezone.utc)
        if (delivery_progress == ProgressStatus.SHIPPED and
                (estimated_delivery is None or
                estimated_delivery > current_time)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estimated delivery date must be in the past for shipped shipments"
            )
        elif ((delivery_progress == ProgressStatus.PLACED or
               delivery_progress == ProgressStatus.IN_TRANSIT) and
               estimated_delivery is not None and estimated_delivery <= current_time):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estimated delivery date must be in the future for placed or in transit shipments"
            )

        return ShipmentCreate.model_validate(valid_shipment)

    async def map_simple_to_create(self, shipment_data: ShipmentCreateSimple, seller_id: UUID) -> ShipmentCreate:
        return ShipmentCreate(
            product=shipment_data.product,
            progress=shipment_data.progress,
            estimated_delivery=shipment_data.estimated_delivery,
            buyer_id=await self._find_user_id_by_username(shipment_data.buyer_username),
            seller_id=seller_id,
        )

    async def _find_user_id_by_username(self, username: str) -> UUID:
        find_by_username = select(User.id).where(User.username == username)
        id = (await self.session.execute(find_by_username)).scalars().one_or_none()
        if id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with username: '{username}' not found"
            )
        return id
