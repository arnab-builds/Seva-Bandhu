"""
Resend HTTPS Email Backend for Django.
Sends emails via Resend's REST API using the official `resend` Python SDK.
"""

import logging
import os
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMultiAlternatives
import resend

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    """
    A Django email backend that transmits emails via the Resend HTTPS API.
    """

    def __init__(self, api_key=None, from_email=None, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = (
            api_key
            or getattr(settings, "RESEND_API_KEY", "")
            or os.environ.get("RESEND_API_KEY", "")
        ).strip()
        self.from_email = (
            from_email
            or getattr(settings, "RESEND_FROM_EMAIL", "")
            or getattr(settings, "DEFAULT_FROM_EMAIL", "")
            or os.environ.get("RESEND_FROM_EMAIL", "")
        ).strip()

    def send_messages(self, email_messages):
        """
        Send messages through the Resend HTTPS API.
        """
        if not email_messages:
            return 0

        if not self.api_key:
            msg = "RESEND_API_KEY is not configured."
            logger.error(msg)
            if not self.fail_silently:
                raise RuntimeError(msg)
            return 0

        resend.api_key = self.api_key

        num_sent = 0
        for message in email_messages:
            try:
                sent = self._send_message(message)
                if sent:
                    num_sent += 1
            except Exception as exc:
                # Sanitize log: log error type only, never exposing credentials
                logger.error("Failed to send email via Resend API: %s", type(exc).__name__)
                if not self.fail_silently:
                    raise

        return num_sent

    def _send_message(self, message):
        from_email = (
            message.from_email
            or self.from_email
            or getattr(settings, "DEFAULT_FROM_EMAIL", "onboarding@resend.dev")
        )
        recipients = list(message.to or [])
        if not recipients:
            return False

        payload = {
            "from": from_email,
            "to": recipients,
            "subject": message.subject or "",
            "text": message.body or "",
        }

        # Check for HTML content
        html_body = None
        if getattr(message, "content_subtype", None) == "html":
            html_body = message.body
        elif isinstance(message, EmailMultiAlternatives):
            for content, mimetype in getattr(message, "alternatives", []):
                if mimetype == "text/html":
                    html_body = content
                    break

        if html_body:
            payload["html"] = html_body

        if message.cc:
            payload["cc"] = list(message.cc)
        if message.bcc:
            payload["bcc"] = list(message.bcc)
        if message.reply_to:
            payload["reply_to"] = list(message.reply_to)

        # Handle attachments if present
        if getattr(message, "attachments", None):
            resend_attachments = []
            for attachment in message.attachments:
                if isinstance(attachment, tuple) and len(attachment) >= 2:
                    filename = attachment[0]
                    content = attachment[1]
                    if isinstance(content, bytes):
                        resend_attachments.append({
                            "filename": filename,
                            "content": list(content),
                        })
                    else:
                        resend_attachments.append({
                            "filename": filename,
                            "content": str(content),
                        })
            if resend_attachments:
                payload["attachments"] = resend_attachments

        response = resend.Emails.send(payload)
        if response and (response.get("id") or isinstance(response, dict)):
            return True
        return False

