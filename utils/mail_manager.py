from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from pydantic import NameEmail

from ..config import email_notification_settings

class MailManager():
    def __init__(self):
        self.fastmail = FastMail(
            ConnectionConfig(
                **email_notification_settings.model_dump()
            )
        )

    async def send_plain_email(self, recipient_list: list[NameEmail], subject: str, body: str):
        await self.fastmail.send_message(
            message=MessageSchema(
                recipients=recipient_list,
                subject=subject,
                body=body,
                subtype=MessageType.plain
            )
        )

    async def send_html_email(self, recipient_list: list[NameEmail], subject: str, body: str):
        await self.fastmail.send_message(
            message=MessageSchema(
                recipients=recipient_list,
                subject=subject,
                body=body,
                subtype=MessageType.html
            )
        )