from uuid import UUID
from pydantic import NameEmail

from ..database.schemas.shipment import ShipmentSummary
from ..database.schemas.user import UserBase
from ..utils.mail_manager import MailManager


class EmailService:
    def __init__(self, manager: MailManager = MailManager()) -> None:
        self.manager = manager
        self.base_url = "http://localhost:5173"

    def _generate_shipment_status_html(
            self,
            shipment: ShipmentSummary,
            recipient_name: str,
            title: str,
            main_message: str,
            highlight_box: str,
            counterparty_label: str,
            counterparty_info: str
    ) -> str:
        delivery_date = shipment.estimated_delivery.strftime("%Y-%m-%d %H:%M") if shipment.estimated_delivery else "N/A"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 20px auto; padding: 0; border-radius: 8px; background-color: #ffffff; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background-color: #007bff; color: #fff; padding: 20px; text-align: center; }}
                .header h2 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 30px 20px; }}
                .highlight-box {{ background-color: #fff3cd; padding: 15px; border-left: 5px solid #ffc107; margin-bottom: 25px; border-radius: 4px; }}
                .field {{ margin-bottom: 12px; border-bottom: 1px solid #f0f0f0; padding-bottom: 8px; }}
                .field:last-child {{ border-bottom: none; }}
                .label {{ font-weight: bold; color: #555; display: inline-block; width: 140px; }}
                .value {{ color: #000; font-weight: 500; }}
                .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; background-color: #e2e6ea; font-weight: bold; font-size: 0.9em; }}
                .btn-container {{ text-align: center; margin-top: 30px; }}
                .btn {{ display: inline-block; background-color: #28a745; color: #ffffff !important; text-decoration: none; padding: 12px 25px; border-radius: 5px; font-weight: bold; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; font-size: 12px; color: #888; text-align: center; border-top: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{title}</h2>
                </div>

                <div class="content">
                    <p>Hello <strong>{recipient_name}</strong>,</p>
                    <p>{main_message}</p>

                    <div class="highlight-box">
                        {highlight_box}
                    </div>

                    <h3>Shipment Details</h3>

                    <div class="field">
                        <span class="label">Product:</span>
                        <span class="value" style="font-size: 1.1em;">{shipment.product}</span>
                    </div>

                    <div class="field">
                        <span class="label">Shipment ID:</span>
                        <span class="value" style="font-family: monospace;">{shipment.id}</span>
                    </div>

                    <div class="field">
                        <span class="label">Status:</span>
                        <span class="status-badge">{shipment.approval_status}</span>
                    </div>

                    <div class="field">
                        <span class="label">{counterparty_label}:</span>
                        <span class="value">{counterparty_info}</span>
                    </div>

                    <div class="field">
                        <span class="label">Estimated Delivery:</span>
                        <span class="value">{delivery_date}</span>
                    </div>

                    <div class="btn-container">
                        <a href="{self.base_url}" class="btn">View Dashboard</a>
                    </div>
                </div>

                <div class="footer">
                    <p>This is an automated message from FastShip system.</p>
                    <p><a href="{self.base_url}" style="color: #007bff;">{self.base_url}</a></p>
                </div>
            </div>
        </body>
        </html>
        """

    async def send_modified_approval(self, shipment: ShipmentSummary, seller: UserBase, buyer: UserBase) -> None:
        buyer_info = f"{buyer.username} ({buyer.email})"
        seller_info = f"{seller.username} ({seller.email})"

        seller_email = NameEmail(seller.full_name, str(seller.email))
        seller_body = self._generate_shipment_status_html(
            shipment=shipment,
            recipient_name=seller.full_name,
            title="Shipment Status Update",
            main_message="The approval status for your shipment has been modified.",
            highlight_box=f"Changes made by: <strong>{buyer_info}</strong>",
            counterparty_label="Buyer",
            counterparty_info=buyer_info
        )

        buyer_email = NameEmail(buyer.full_name, str(buyer.email))
        buyer_body = self._generate_shipment_status_html(
            shipment=shipment,
            recipient_name=buyer.full_name,
            title="Order Status Changed",
            main_message="The status of your purchase was recently updated.",
            highlight_box=f"<strong>Was this you?</strong><br>If you didn't authorize this change, please contact support immediately.",
            counterparty_label="Seller",
            counterparty_info=seller_info
        )

        await self.manager.send_html_email(
            [seller_email],
            subject=f"Shipment '{shipment.product}' Status Update",
            body=seller_body
        )

        await self.manager.send_html_email(
            [buyer_email],
            subject=f"Order '{shipment.product}' Update",
            body=buyer_body
        )

    async def send_shipment_created(self, shipment: ShipmentSummary, seller: UserBase, buyer: UserBase) -> None:
        buyer_info = f"{buyer.username} ({buyer.email})"
        seller_info = f"{seller.username} ({seller.email})"

        buyer_email = NameEmail(buyer.full_name, str(buyer.email))
        buyer_body = self._generate_shipment_status_html(
            shipment=shipment,
            recipient_name=buyer.full_name,
            title="Action Required: New Shipment Created",
            main_message=f"A new shipment containing '<strong>{shipment.product}</strong>' has been initiated for you.",
            highlight_box="<strong>Action Required:</strong><br>Please log in to your dashboard to <strong>Approve</strong> or <strong>Reject</strong> this shipment to proceed.",
            counterparty_label="Seller",
            counterparty_info=seller_info
        )

        seller_email = NameEmail(seller.full_name, str(seller.email))
        seller_body = self._generate_shipment_status_html(
            shipment=shipment,
            recipient_name=seller.full_name,
            title="Shipment Created Successfully",
            main_message=f"Your shipment '<strong>{shipment.product}</strong>' has been successfully registered in the system.",
            highlight_box="<strong>Status: Pending Approval</strong><br>We have notified the buyer. You will receive an automatic update once they respond.",
            counterparty_label="Buyer",
            counterparty_info=buyer_info
        )

        await self.manager.send_html_email(
            [buyer_email],
            subject=f"Action Required: New Shipment '{shipment.product}'",
            body=buyer_body
        )

        await self.manager.send_html_email(
            [seller_email],
            subject=f"Shipment Created: '{shipment.product}'",
            body=seller_body
        )

email_service = EmailService()