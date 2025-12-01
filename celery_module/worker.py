import asyncio

from .app import app
from ..database.schemas.shipment import ShipmentSummary
from ..services.email_service import email_service
from ..database.schemas.user import UserBase

@app.task(name="send_verification_email_task")
def send_verification_email_task(user_data: dict, token: str):
    user = UserBase(**user_data)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(email_service.send_verification_email(user, token))
    except RuntimeError:
        asyncio.run(email_service.send_verification_email(user, token))

    return f"Verification email sent to {user.email}"


@app.task(name="send_password_reset_email")
def send_password_reset_email_task(user_data: dict, token: str):
    user = UserBase(**user_data)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(email_service.send_password_reset_email(user, token))
    except RuntimeError:
        asyncio.run(email_service.send_password_reset_email(user, token))

    return f"Password reset email sent to {user.email}"


@app.task(name="send_shipment_created_email")
def send_shipment_created_email_task(shipment_data: dict, seller_data: dict, buyer_data: dict):
    shipment = ShipmentSummary(**shipment_data)
    seller = UserBase(**seller_data)
    buyer = UserBase(**buyer_data)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(email_service.send_shipment_created_email(shipment, seller, buyer))
    except RuntimeError:
        asyncio.run(email_service.send_shipment_created_email(shipment, seller, buyer))

    return f"Shipment created email sent to {buyer.email}"


@app.task(name="send_modified_approval_email")
def send_modified_approval_email_task(shipment_data: dict, seller_data: dict, buyer_data: dict):
    shipment = ShipmentSummary(**shipment_data)
    seller = UserBase(**seller_data)
    buyer = UserBase(**buyer_data)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(email_service.send_modified_approval_email(shipment, seller, buyer))
    except RuntimeError:
        asyncio.run(email_service.send_modified_approval_email(shipment, seller, buyer))

    return f"Modified approval email sent to {seller.email} and {buyer.email}"