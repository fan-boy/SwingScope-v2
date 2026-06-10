"""
Email sender — SMTP with TLS.
Works with Gmail App Passwords, Resend SMTP, SendGrid, Mailgun, etc.
"""
import asyncio
import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    to: str
    subject: str
    html: str
    text: str


class EmailSender:
    def __init__(self, host: str, port: int, username: str, password: str, from_addr: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_addr = from_addr

    async def send(self, msg: EmailMessage) -> None:
        """Send email in a thread pool to avoid blocking the event loop."""
        await asyncio.get_event_loop().run_in_executor(None, self._send_sync, msg)

    def _send_sync(self, msg: EmailMessage) -> None:
        mime = MIMEMultipart("alternative")
        mime["Subject"] = msg.subject
        mime["From"] = self.from_addr
        mime["To"] = msg.to
        mime.attach(MIMEText(msg.text, "plain"))
        mime.attach(MIMEText(msg.html, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP(self.host, self.port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(self.username, self.password)
            server.sendmail(self.from_addr, msg.to, mime.as_string())
            logger.info("Email sent to %s: %s", msg.to, msg.subject)


def get_email_sender() -> EmailSender | None:
    """Return configured sender or None if SMTP not configured."""
    from app.core.config import settings
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.alert_email_to]):
        return None
    return EmailSender(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        from_addr=settings.smtp_from or settings.smtp_username,
    )
