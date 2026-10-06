"""
Brevo HTTPS Transactional Email Backend for Django.
Sends emails via Brevo's REST API using the official `brevo-python` SDK over HTTPS (Port 443).
"""

import base64
import email.utils
import logging
import os
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMultiAlternatives
from brevo import Brevo
from brevo.core import ApiError

logger = logging.getLogger(__name__)


def _parse_recipient_or_sender(addr_str, default_name=""):
    """
    Parses a string like 'Name <email@example.com>' or 'email@example.com'
    into a dictionary {'email': str, 'name': str}.
    """
    if not addr_str:
        return None
    name, addr = email.utils.parseaddr(addr_str)
    addr = addr.strip()
    if not addr:
        return None
    res = {"email": addr}
    final_name = (name or default_name).strip()
    if final_name:
        res["name"] = final_name
    return res


class BrevoEmailBackend(BaseEmailBackend):
    """
    A Django email backend that transmits transactional emails via the Brevo HTTPS API.
    """

    def __init__(self, api_key=None, from_email=None, from_name=None, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = (
            api_key
            or getattr(settings, "BREVO_API_KEY", "")
            or os.environ.get("BREVO_API_KEY", "")
        ).strip()

        configured_from_email = (
            getattr(settings, "BREVO_FROM_EMAIL", "")
            or getattr(settings, "DEFAULT_FROM_EMAIL", "")
            or os.environ.get("BREVO_FROM_EMAIL", "")
        ).strip()

        self.from_name = (
            from_name
            or getattr(settings, "BREVO_FROM_NAME", "")
            or os.environ.get("BREVO_FROM_NAME", "")
        ).strip()

        self.from_email = (from_email or configured_from_email).strip()
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = Brevo(api_key=self.api_key)
        return self._client

    def send_messages(self, email_messages):
        """
        Send messages through the Brevo Transactional Email HTTPS API.
        """
        if not email_messages:
            return 0

        if not self.api_key:
            msg = "BREVO_API_KEY is not configured."
            logger.error(msg)
            if not self.fail_silently:
                raise RuntimeError(msg)
            return 0

        num_sent = 0
        client = self._get_client()

        for message in email_messages:
            try:
                sent = self._send_message(client, message)
                if sent:
                    num_sent += 1
            except Exception as exc:
                # Sanitize log: log error type only, never exposing credentials or raw payload
                if isinstance(exc, ApiError):
                    logger.error("Failed to send email via Brevo API (status_code=%s): %s", exc.status_code, type(exc).__name__)
                else:
                    logger.error("Failed to send email via Brevo API: %s", type(exc).__name__)
                if not self.fail_silently:
                    raise

        return num_sent

    def _send_message(self, client, message):
        raw_from = (
            message.from_email
            or self.from_email
            or getattr(settings, "DEFAULT_FROM_EMAIL", "")
        )
        sender_dict = _parse_recipient_or_sender(raw_from, default_name=self.from_name)
        if not sender_dict or not sender_dict.get("email"):
            return False

        # Build recipient list
        to_items = []
        for recipient in (message.to or []):
            parsed = _parse_recipient_or_sender(recipient)
            if parsed:
                to_items.append(parsed)

        if not to_items:
            return False

        # Extract message bodies
        text_body = message.body or ""
        html_body = None

        if getattr(message, "content_subtype", None) == "html":
            html_body = message.body
        elif isinstance(message, EmailMultiAlternatives):
            for content, mimetype in getattr(message, "alternatives", []):
                if mimetype == "text/html":
                    html_body = content
                    break

        request_kwargs = {
            "subject": message.subject or "",
            "sender": sender_dict,
            "to": to_items,
        }

        # Provide body content
        if html_body:
            request_kwargs["html_content"] = html_body
            if text_body:
                request_kwargs["text_content"] = text_body
        else:
            request_kwargs["text_content"] = text_body

        # Handle CC
        if message.cc:
            cc_items = []
            for recipient in message.cc:
                parsed = _parse_recipient_or_sender(recipient)
                if parsed:
                    cc_items.append(parsed)
            if cc_items:
                request_kwargs["cc"] = cc_items

        # Handle BCC
        if message.bcc:
            bcc_items = []
            for recipient in message.bcc:
                parsed = _parse_recipient_or_sender(recipient)
                if parsed:
                    bcc_items.append(parsed)
            if bcc_items:
                request_kwargs["bcc"] = bcc_items

        # Handle reply-to (Brevo takes a single object for replyTo)
        if message.reply_to:
            first_reply = message.reply_to[0]
            parsed_reply = _parse_recipient_or_sender(first_reply)
            if parsed_reply:
                request_kwargs["reply_to"] = parsed_reply

        # Handle attachments (Base64 encoded)
        if getattr(message, "attachments", None):
            brevo_attachments = []
            for attachment in message.attachments:
                if isinstance(attachment, tuple) and len(attachment) >= 2:
                    filename = attachment[0]
                    content = attachment[1]
                    if isinstance(content, bytes):
                        b64_content = base64.b64encode(content).decode("utf-8")
                    else:
                        b64_content = base64.b64encode(str(content).encode("utf-8")).decode("utf-8")
                    brevo_attachments.append({
                        "name": filename,
                        "content": b64_content,
                    })
            if brevo_attachments:
                request_kwargs["attachment"] = brevo_attachments

        response = client.transactional_emails.send_transac_email(**request_kwargs)
        if response and (getattr(response, "message_id", None) or getattr(response, "message_ids", None)):
            return True
        return False
