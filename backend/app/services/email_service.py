import base64
import logging
import smtplib
from concurrent.futures import ThreadPoolExecutor
from email.message import EmailMessage
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)


def _build_message(
    *,
    subject: str,
    to_email: str,
    html: str,
    text: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(text or "This email requires an HTML-capable client.")
    msg.add_alternative(html, subtype="html")
    if attachments:
        for att in attachments:
            data = att.get("content") or b""
            fn = att.get("filename") or "attachment.bin"
            subtype = (att.get("content_type") or "application/octet-stream").split(
                "/"
            )[-1]
            main = (att.get("content_type") or "application/octet-stream").split("/")[0]
            msg.add_attachment(data, maintype=main, subtype=subtype, filename=fn)
    return msg


def _send_sendgrid_sync(
    *,
    subject: str,
    to_email: str,
    html: str,
    text: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> None:
    content: list[dict[str, str]] = []
    if text:
        content.append({"type": "text/plain", "value": text})
    content.append({"type": "text/html", "value": html})
    body: dict[str, Any] = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {
            "email": settings.SENDGRID_FROM_EMAIL.strip(),
            "name": settings.SENDGRID_FROM_NAME.strip() or "Vendora",
        },
        "subject": subject,
        "content": content,
    }
    if attachments:
        body["attachments"] = [
            {
                "content": base64.b64encode(a.get("content") or b"").decode("ascii"),
                "filename": a.get("filename") or "file.bin",
                "type": a.get("content_type") or "application/octet-stream",
                "disposition": "attachment",
            }
            for a in attachments
        ]
    resp = httpx.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=40.0,
    )
    if resp.status_code >= 400:
        logger.error("SendGrid HTTP %s: %s", resp.status_code, resp.text[:500])
        resp.raise_for_status()


def _send_mailgun_sync(
    *,
    subject: str,
    to_email: str,
    html: str,
    text: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> None:
    url = (
        f"{settings.MAILGUN_API_BASE.rstrip('/')}/v3/{settings.MAILGUN_DOMAIN}/messages"
    )
    data = {
        "from": settings.MAILGUN_FROM,
        "to": to_email,
        "subject": subject,
        "html": html,
    }
    if text:
        data["text"] = text
    file_list: list[tuple[str, tuple[str, bytes, str]]] = []
    if attachments:
        for a in attachments:
            fn = a.get("filename") or "file.bin"
            ct = a.get("content_type") or "application/octet-stream"
            file_list.append(("attachment", (fn, a.get("content") or b"", ct)))
    resp = httpx.post(
        url,
        auth=("api", settings.MAILGUN_API_KEY),
        data=data,
        files=file_list if file_list else None,
        timeout=40.0,
    )
    if resp.status_code >= 400:
        logger.error("Mailgun HTTP %s: %s", resp.status_code, resp.text[:500])
        resp.raise_for_status()


def _send_resend_sync(
    *,
    subject: str,
    to_email: str,
    html: str,
    text: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "from": settings.RESEND_FROM,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text
    if attachments:
        payload["attachments"] = [
            {
                "filename": a.get("filename") or "file.bin",
                "content": base64.b64encode(a.get("content") or b"").decode("ascii"),
            }
            for a in attachments
        ]
    resp = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=40.0,
    )
    if resp.status_code >= 400:
        logger.error("Resend HTTP %s: %s", resp.status_code, resp.text[:500])
        resp.raise_for_status()


def _send_sync(
    *,
    subject: str,
    to_email: str,
    html: str,
    text: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> None:
    if settings.RESEND_API_KEY:
        _send_resend_sync(
            subject=subject,
            to_email=to_email,
            html=html,
            text=text,
            attachments=attachments,
        )
        return

    if settings.SENDGRID_API_KEY:
        _send_sendgrid_sync(
            subject=subject,
            to_email=to_email,
            html=html,
            text=text,
            attachments=attachments,
        )
        return

    if settings.MAILGUN_API_KEY and settings.MAILGUN_DOMAIN and settings.MAILGUN_FROM:
        _send_mailgun_sync(
            subject=subject,
            to_email=to_email,
            html=html,
            text=text,
            attachments=attachments,
        )
        return

    if not settings.SMTP_HOST:
        logger.info(
            "No email provider configured (set RESEND_API_KEY, SENDGRID_API_KEY, "
            "Mailgun, or SMTP_HOST) — skipping send (subject=%s, to=%s)",
            subject,
            to_email,
        )
        return

    msg = _build_message(
        subject=subject,
        to_email=to_email,
        html=html,
        text=text,
        attachments=attachments,
    )

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            server.ehlo()
            try:
                server.starttls()
                server.ehlo()
            except Exception:
                logger.debug(
                    "SMTP STARTTLS not supported or failed; continuing without TLS"
                )

            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception:
        logger.exception("Email send failed (subject=%s, to=%s)", subject, to_email)
        raise


async def send_email(
    *,
    subject: str,
    to_email: str,
    html: str,
    text: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> None:
    """Async-safe: runs synchronous providers in a worker thread."""

    import asyncio

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        _executor,
        lambda: _send_sync(
            subject=subject,
            to_email=to_email,
            html=html,
            text=text,
            attachments=attachments,
        ),
    )
