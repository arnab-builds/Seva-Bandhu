"""
Tests for Resend HTTPS Email Backend and email flows in Seva Bandhu.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.urls import reverse
import resend.exceptions as resend_exceptions

from core.email_backend import ResendEmailBackend
from core.views import _send_customer_verification_email


class ResendEmailBackendUnitTests(TestCase):
    def test_backend_initialization_defaults(self):
        with override_settings(RESEND_API_KEY="re_test_key_123", RESEND_FROM_EMAIL="test@sevabandhu.in"):
            backend = ResendEmailBackend()
            self.assertEqual(backend.api_key, "re_test_key_123")
            self.assertEqual(backend.from_email, "test@sevabandhu.in")

    def test_missing_api_key_raises_when_not_fail_silently(self):
        backend = ResendEmailBackend(api_key="", fail_silently=False)
        msg = EmailMessage("Test", "Body", "from@example.com", ["to@example.com"])
        with self.assertRaises(RuntimeError) as ctx:
            backend.send_messages([msg])
        self.assertIn("RESEND_API_KEY is not configured", str(ctx.exception))

    def test_missing_api_key_returns_zero_when_fail_silently(self):
        backend = ResendEmailBackend(api_key="", fail_silently=True)
        msg = EmailMessage("Test", "Body", "from@example.com", ["to@example.com"])
        sent_count = backend.send_messages([msg])
        self.assertEqual(sent_count, 0)

    @patch("resend.Emails.send")
    def test_send_plain_text_message(self, mock_send):
        mock_send.return_value = {"id": "resend_msg_001"}
        backend = ResendEmailBackend(api_key="re_valid_key", from_email="support@sevabandhu.in")

        msg = EmailMessage(
            subject="Welcome to Seva Bandhu",
            body="Hello, thank you for joining.",
            from_email="custom@sevabandhu.in",
            to=["user@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            reply_to=["reply@example.com"],
        )
        sent = backend.send_messages([msg])
        self.assertEqual(sent, 1)

        mock_send.assert_called_once()
        payload = mock_send.call_args[0][0]
        self.assertEqual(payload["from"], "custom@sevabandhu.in")
        self.assertEqual(payload["to"], ["user@example.com"])
        self.assertEqual(payload["subject"], "Welcome to Seva Bandhu")
        self.assertEqual(payload["text"], "Hello, thank you for joining.")
        self.assertEqual(payload["cc"], ["cc@example.com"])
        self.assertEqual(payload["bcc"], ["bcc@example.com"])
        self.assertEqual(payload["reply_to"], ["reply@example.com"])

    @patch("resend.Emails.send")
    def test_send_html_message_via_content_subtype(self, mock_send):
        mock_send.return_value = {"id": "resend_msg_002"}
        backend = ResendEmailBackend(api_key="re_valid_key", from_email="support@sevabandhu.in")

        msg = EmailMessage(
            subject="HTML Notice",
            body="<h1>Hello</h1>",
            from_email="support@sevabandhu.in",
            to=["user@example.com"],
        )
        msg.content_subtype = "html"
        sent = backend.send_messages([msg])
        self.assertEqual(sent, 1)

        payload = mock_send.call_args[0][0]
        self.assertEqual(payload["html"], "<h1>Hello</h1>")

    @patch("resend.Emails.send")
    def test_send_multipart_alternative_html(self, mock_send):
        mock_send.return_value = {"id": "resend_msg_003"}
        backend = ResendEmailBackend(api_key="re_valid_key", from_email="support@sevabandhu.in")

        msg = EmailMultiAlternatives(
            subject="Resolution Details",
            body="Plain text summary",
            from_email="support@sevabandhu.in",
            to=["customer@example.com"],
        )
        msg.attach_alternative("<div><p>HTML resolution</p></div>", "text/html")
        sent = backend.send_messages([msg])
        self.assertEqual(sent, 1)

        payload = mock_send.call_args[0][0]
        self.assertEqual(payload["text"], "Plain text summary")
        self.assertEqual(payload["html"], "<div><p>HTML resolution</p></div>")

    @patch("resend.Emails.send")
    def test_send_with_attachments(self, mock_send):
        mock_send.return_value = {"id": "resend_msg_004"}
        backend = ResendEmailBackend(api_key="re_valid_key", from_email="billing@sevabandhu.in")

        msg = EmailMessage(
            subject="Invoice #42",
            body="Invoice attached.",
            from_email="billing@sevabandhu.in",
            to=["customer@example.com"],
        )
        pdf_data = b"%PDF-1.4 test invoice content"
        msg.attach("invoice_42.pdf", pdf_data, "application/pdf")

        sent = backend.send_messages([msg])
        self.assertEqual(sent, 1)

        payload = mock_send.call_args[0][0]
        self.assertIn("attachments", payload)
        self.assertEqual(len(payload["attachments"]), 1)
        att = payload["attachments"][0]
        self.assertEqual(att["filename"], "invoice_42.pdf")
        self.assertEqual(att["content"], list(pdf_data))

    @patch("resend.Emails.send")
    def test_api_failure_raises_when_not_fail_silently(self, mock_send):
        mock_send.side_effect = resend_exceptions.ResendError(
            code=401,
            error_type="invalid_api_key",
            message="Invalid API key",
            suggested_action="Check your API key in dashboard.",
        )
        backend = ResendEmailBackend(api_key="re_invalid", fail_silently=False)
        msg = EmailMessage("Subject", "Body", "from@test.com", ["to@test.com"])

        with self.assertRaises(resend_exceptions.ResendError):
            backend.send_messages([msg])

    @patch("resend.Emails.send")
    def test_api_failure_caught_when_fail_silently(self, mock_send):
        mock_send.side_effect = resend_exceptions.ResendError(
            code=500,
            error_type="server_error",
            message="Internal Server Error",
            suggested_action="Retry later.",
        )
        backend = ResendEmailBackend(api_key="re_valid", fail_silently=True)
        msg = EmailMessage("Subject", "Body", "from@test.com", ["to@test.com"])

        sent = backend.send_messages([msg])
        self.assertEqual(sent, 0)


@override_settings(
    EMAIL_BACKEND="core.email_backend.ResendEmailBackend",
    RESEND_API_KEY="re_mock_test_key",
    DEFAULT_FROM_EMAIL="notifications@sevabandhu.in",
)
class DjangoEmailIntegrationTests(TestCase):
    @patch("resend.Emails.send")
    def test_django_send_mail_dispatches_to_resend_backend(self, mock_send):
        mock_send.return_value = {"id": "resend_mock_id_999"}

        count = send_mail(
            subject="OTP Verification",
            message="Your OTP is 123456",
            from_email="notifications@sevabandhu.in",
            recipient_list=["customer@example.com"],
            fail_silently=False,
        )
        self.assertEqual(count, 1)
        mock_send.assert_called_once()
        payload = mock_send.call_args[0][0]
        self.assertEqual(payload["to"], ["customer@example.com"])
        self.assertIn("123456", payload["text"])

    @patch("resend.Emails.send")
    def test_customer_verification_email_helper_calls_resend(self, mock_send):
        mock_send.return_value = {"id": "resend_otp_msg"}

        _send_customer_verification_email("customer_otp@example.com", "654321")

        mock_send.assert_called_once()
        payload = mock_send.call_args[0][0]
        self.assertEqual(payload["to"], ["customer_otp@example.com"])
        self.assertIn("654321", payload["text"])
        self.assertEqual(payload["subject"], "Your Seva Bandhu verification code")

    @patch("resend.Emails.send")
    def test_customer_send_verification_endpoint_calls_resend(self, mock_send):
        mock_send.return_value = {"id": "resend_endpoint_msg"}

        url = reverse("send_verification_email")
        response = self.client.post(
            url,
            data='{"email": "customer_signup_test@example.com"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("code has been sent", data["message"])

        mock_send.assert_called_once()
        payload = mock_send.call_args[0][0]
        self.assertEqual(payload["to"], ["customer_signup_test@example.com"])
