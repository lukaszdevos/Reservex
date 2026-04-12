"""I/O-bound worker for SMTP email sending via ThreadPoolExecutor.

Layer: infrastructure/workers
_send_smtp_blocking runs inside a thread to avoid blocking the event loop.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from concurrent.futures import ThreadPoolExecutor
from email.message import EmailMessage

_log = logging.getLogger(__name__)

_SMTP_HOST: str = "localhost"
_SMTP_PORT: int = 25


def _send_smtp_blocking(to: str, subject: str, body: str) -> None:
    """Send an email synchronously - runs inside a thread pool worker."""
    msg = EmailMessage()
    msg["From"] = "noreply@reservex.local"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=10) as smtp:
            smtp.send_message(msg)
    except OSError as exc:
        _log.warning("smtp_send_failed to=%s error=%s", to, exc)


async def send_email(
    to: str,
    subject: str,
    body: str,
    thread_pool: ThreadPoolExecutor,
) -> None:
    """Offload SMTP send to a thread via ThreadPoolExecutor."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(thread_pool, _send_smtp_blocking, to, subject, body)
