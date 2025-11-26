import asyncio

from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType

from config import email_notification_settings

fastmail = FastMail(
    ConnectionConfig(
        **email_notification_settings.model_dump()
    )
)

async def send_email():
    await fastmail.send_message(
        message=MessageSchema(
            recipients=["akuchera7@gmail.com"],
            subject="First SMTP Email!",
            body="What you know about rolling down to the deep",
            subtype=MessageType.plain
        )
    )
    print("Email sent!")

asyncio.run(send_email())