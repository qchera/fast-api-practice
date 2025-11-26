from typing import List
from uuid import UUID

from fastapi import APIRouter, status, HTTPException

from ..database.models.shipment import Shipment
from ..database.schemas.shipment import ShipmentSummary, ShipmentCreateSimple, ShipmentStatusUpdate
from ..dependencies import ShipmentServiceDep, UserDep

router = APIRouter(prefix="/shipments", tags=["Shipments"])

@router.get("/", response_model=List[ShipmentSummary])
async def get_all_shipments(current_user: UserDep,
                            shipment_service: ShipmentServiceDep) -> List[ShipmentSummary]:
    return await shipment_service.get_all_shipments()


@router.get("/my", response_model=List[ShipmentSummary])
async def get_my_shipments(
        current_user: UserDep,
        service: ShipmentServiceDep
):
    shipments = await service.get_shipments_by_user_id(current_user.id)
    return shipments

@router.get("/{shipment_id}", response_model=Shipment)
async def get_shipment_by_id(shipment_id: UUID,
                             shipment_service: ShipmentServiceDep) -> Shipment:
    return await shipment_service.get_shipment_by_id(shipment_id)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ShipmentSummary)
async def create_shipment(current_user: UserDep,
                          shipment_data_simple: ShipmentCreateSimple,
                          shipment_service: ShipmentServiceDep) -> ShipmentSummary:
    if current_user.username == shipment_data_simple.buyer_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Buyer and seller cannot be the same user"
        )
    return await shipment_service.create_shipment(shipment_data_simple, current_user.id)

@router.patch("/{shipment_id}/approval", status_code=status.HTTP_200_OK, response_model=ShipmentSummary)
async def update_shipment_approval_status(shipment_service: ShipmentServiceDep,
                                          shipment_id: UUID,
                                          status_update: ShipmentStatusUpdate) -> ShipmentSummary:
     return await shipment_service.update_shipment_approval_status(shipment_id, status_update.approval_status)

'''
@router.put("/{shipment_id}", response_model=Shipment)
async def update_shipment(shipment_id: UUID,
                          shipment_update: ShipmentSummary,
                          shipment_service: ShipmentServiceDep) -> Shipment:
    return await shipment_service.update_shipment(shipment_id, shipment_update)
'''

@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipment(shipment_id: UUID,
                          shipment_service: ShipmentServiceDep) -> None:
    await shipment_service.delete_shipment(shipment_id)