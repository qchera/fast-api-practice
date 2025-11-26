from uuid import UUID

from fastapi.encoders import jsonable_encoder

from ..utils.socket_manager import socket_manager, SocketConnectionManager
from ..database.schemas.shipment import ShipmentSummary


class SocketMessageService:
    def __init__(self, manager: SocketConnectionManager = socket_manager):
        self.manager = manager

    async def update_sale_message(self, seller_id: UUID, shipment_summary: ShipmentSummary) -> None:
        message = {
            "type": "SALE_UPDATE",
            "payload": jsonable_encoder(shipment_summary)
        }
        await self.manager.send_message(seller_id, message)

    async def add_pending_purchase_message(self, buyer_id: UUID, shipment_summary: ShipmentSummary) -> None:
        message = {
            "type": "PURCHASE_ADD",
            "payload": jsonable_encoder(shipment_summary)
        }
        await self.manager.send_message(buyer_id, message)

socket_message_service = SocketMessageService()