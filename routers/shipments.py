from typing import List
from uuid import UUID

from fastapi import APIRouter, status

from ..database.models import Shipment, ShipmentCreate, ShipmentUpdate, ShipmentRead
from ..dependencies import ShipmentServiceDep, UserDep

router = APIRouter(prefix="/shipments", tags=["Shipments"])

@router.get("/", response_model=List[Shipment])
async def get_all_shipments(current_user: UserDep,
                            shipment_service: ShipmentServiceDep) -> List[Shipment]:
    return await shipment_service.get_all_shipments()


@router.get("/my", response_model=List[ShipmentRead])
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

@router.post("/fill", status_code=status.HTTP_201_CREATED)
async def fill_table(current_user: UserDep,
                     shipment_service: ShipmentServiceDep) -> None:
    await shipment_service.fill_table(current_user.id)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Shipment)
async def create_shipment(current_user: UserDep,
                          shipment_data: ShipmentCreate,
                          shipment_service: ShipmentServiceDep) -> Shipment:
    return await shipment_service.create_shipment(shipment_data, current_user.id)

@router.put("/{shipment_id}", response_model=Shipment)
async def update_shipment(shipment_id: UUID,
                          shipment_update: ShipmentUpdate,
                          shipment_service: ShipmentServiceDep) -> Shipment:
    return await shipment_service.update_shipment(shipment_id, shipment_update)

@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipment(shipment_id: UUID,
                          shipment_service: ShipmentServiceDep) -> None:
    await shipment_service.delete_shipment(shipment_id)