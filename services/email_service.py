from pathlib import Path
from fastapi.templating import Jinja2Templates
from pydantic import NameEmail

from ..config import app_settings
from ..database.schemas.shipment import ShipmentSummary
from ..database.schemas.user import UserBase
from ..utils.mail_manager import MailManager

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "email_templates"))

class EmailService:
    def __init__(self, manager: MailManager = MailManager()) -> None:
        self.manager = manager
        self.base_url = app_settings.APP_CLIENT_DOMAIN
        self.protocol = 'http://'

    def _render_template(self, template_name: str, context: dict) -> str:
        context.update({"base_url": self.protocol +  self.base_url})
        template = templates.get_template(template_name)
        return template.render(context)

    async def send_verification_email(self, user: UserBase, token: str) -> None:
        verification_link = f"{self.protocol}{self.base_url}/verify-email?token={token}"
        user_email = NameEmail(user.full_name, str(user.email))

        email_body = self._render_template("action.html", {
            "title": "Verify Your Email Address",
            "recipient_name": user.full_name,
            "main_message": "Thank you for registering with FastShip! To activate your account, please verify your email.",
            "button_text": "Verify Email",
            "button_link": verification_link
        })

        await self.manager.send_html_email(
            [user_email],
            subject="FastShip - Verify your email",
            body=email_body
        )

    async def send_modified_approval(self, shipment: ShipmentSummary, seller: UserBase, buyer: UserBase) -> None:
        buyer_info = f"{buyer.username} ({buyer.email})"
        seller_info = f"{seller.username} ({seller.email})"
        delivery_date = shipment.estimated_delivery.strftime("%Y-%m-%d %H:%M") if shipment.estimated_delivery else "N/A"

        seller_email = NameEmail(seller.full_name, str(seller.email))
        seller_body = self._render_template("shipment_status.html", {
            "title": "Shipment Status Update",
            "recipient_name": seller.full_name,
            "main_message": "The approval status for your shipment has been modified.",
            "highlight_box": f"Changes made by: <strong>{buyer_info}</strong>",
            "shipment": shipment,
            "delivery_date": delivery_date,
            "counterparty_label": "Buyer",
            "counterparty_info": buyer_info
        })

        buyer_email = NameEmail(buyer.full_name, str(buyer.email))
        buyer_body = self._render_template("shipment_status.html", {
            "title": "Order Status Changed",
            "recipient_name": buyer.full_name,
            "main_message": "The status of your purchase was recently updated.",
            "highlight_box": "<strong>Was this you?</strong><br>If you didn't authorize this change, contact support.",
            "shipment": shipment,
            "delivery_date": delivery_date,
            "counterparty_label": "Seller",
            "counterparty_info": seller_info
        })

        await self.manager.send_html_email([seller_email], subject=f"Shipment Update: {shipment.product}", body=seller_body)
        await self.manager.send_html_email([buyer_email], subject=f"Order Update: {shipment.product}", body=buyer_body)

    async def send_shipment_created(self, shipment: ShipmentSummary, seller: UserBase, buyer: UserBase) -> None:
        buyer_info = f"{buyer.username} ({buyer.email})"
        seller_info = f"{seller.username} ({seller.email})"
        delivery_date = shipment.estimated_delivery.strftime("%Y-%m-%d %H:%M") if shipment.estimated_delivery else "N/A"

        buyer_email = NameEmail(buyer.full_name, str(buyer.email))
        buyer_body = self._render_template("shipment_status.html", {
            "title": "Action Required: New Shipment",
            "recipient_name": buyer.full_name,
            "main_message": f"A new shipment containing '<strong>{shipment.product}</strong>' has been initiated.",
            "highlight_box": "<strong>Action Required:</strong><br>Please log in to Approve or Reject this shipment.",
            "shipment": shipment,
            "delivery_date": delivery_date,
            "counterparty_label": "Seller",
            "counterparty_info": seller_info
        })

        seller_email = NameEmail(seller.full_name, str(seller.email))
        seller_body = self._render_template("shipment_status.html", {
            "title": "Shipment Created",
            "recipient_name": seller.full_name,
            "main_message": f"Your shipment '<strong>{shipment.product}</strong>' has been registered.",
            "highlight_box": "<strong>Status: Pending Approval</strong><br>Waiting for buyer response.",
            "shipment": shipment,
            "delivery_date": delivery_date,
            "counterparty_label": "Buyer",
            "counterparty_info": buyer_info
        })

        await self.manager.send_html_email([buyer_email], subject=f"Action Required: {shipment.product}", body=buyer_body)
        await self.manager.send_html_email([seller_email], subject=f"Shipment Created: {shipment.product}", body=seller_body)

email_service = EmailService()