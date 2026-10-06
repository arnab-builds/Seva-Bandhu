"""
Tests for Brevo HTTPS Transactional Email Backend and email flows in Seva Bandhu.
"""

import base64
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.urls import reverse
from brevo.core import ApiError
from brevo.transactional_emails.types import SendTransacEmailResponse

from core.email_backend import BrevoEmailBackend, _parse_recipient_or_sender
from core.views import _send_customer_verification_email, send_invoice_email
from core.models import User, customer_signup, SupportTicket


class BrevoEmailBackendUnitTests(TestCase):
    def test_parse_recipient_or_sender(self):
        self.assertIsNone(_parse_recipient_or_sender(""))
        self.assertIsNone(_parse_recipient_or_sender(None))
        self.assertEqual(
            _parse_recipient_or_sender("john@example.com"),
            {"email": "john@example.com"},
        )
        self.assertEqual(
            _parse_recipient_or_sender("John Doe <john@example.com>"),
            {"email": "john@example.com", "name": "John Doe"},
        )
        self.assertEqual(
            _parse_recipient_or_sender("john@example.com", default_name="Seva Bandhu"),
            {"email": "john@example.com", "name": "Seva Bandhu"},
        )

    def test_backend_initialization_defaults(self):
        with override_settings(
            BREVO_API_KEY="xkeysib-mock-key-123",
            BREVO_FROM_EMAIL="support@sevabandhu.in",
            BREVO_FROM_NAME="Seva Bandhu",
        ):
            backend = BrevoEmailBackend()
            self.assertEqual(backend.api_key, "xkeysib-mock-key-123")
            self.assertEqual(backend.from_email, "support@sevabandhu.in")
            self.assertEqual(backend.from_name, "Seva Bandhu")

    def test_missing_api_key_raises_when_not_fail_silently(self):
        backend = BrevoEmailBackend(api_key="", fail_silently=False)
        msg = EmailMessage("Test", "Body", "from@example.com", ["to@example.com"])
        with self.assertRaises(RuntimeError) as ctx:
            backend.send_messages([msg])
        self.assertIn("BREVO_API_KEY is not configured", str(ctx.exception))

    def test_missing_api_key_returns_zero_when_fail_silently(self):
        backend = BrevoEmailBackend(api_key="", fail_silently=True)
        msg = EmailMessage("Test", "Body", "from@example.com", ["to@example.com"])
        sent_count = backend.send_messages([msg])
        self.assertEqual(sent_count, 0)

    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    def test_send_plain_text_message(self, mock_send):
        mock_send.return_value = SendTransacEmailResponse(message_id="<brevo_msg_001@smtp-relay.mailin.fr>")
        backend = BrevoEmailBackend(
            api_key="xkeysib-valid",
            from_email="support@sevabandhu.in",
            from_name="Seva Bandhu Support",
        )

        msg = EmailMessage(
            subject="Welcome to Seva Bandhu",
            body="Hello, thank you for joining.",
            from_email="Custom Sender <custom@sevabandhu.in>",
            to=["user@example.com"],
            cc=["CC Person <cc@example.com>"],
            bcc=["bcc@example.com"],
            reply_to=["reply@example.com"],
        )
        sent = backend.send_messages([msg])
        self.assertEqual(sent, 1)

        mock_send.assert_called_once()
        kwargs = mock_send.call_args[1]
        self.assertEqual(kwargs["sender"], {"email": "custom@sevabandhu.in", "name": "Custom Sender"})
        self.assertEqual(kwargs["to"], [{"email": "user@example.com"}])
        self.assertEqual(kwargs["subject"], "Welcome to Seva Bandhu")
        self.assertEqual(kwargs["text_content"], "Hello, thank you for joining.")
        self.assertEqual(kwargs["cc"], [{"email": "cc@example.com", "name": "CC Person"}])
        self.assertEqual(kwargs["bcc"], [{"email": "bcc@example.com"}])
        self.assertEqual(kwargs["reply_to"], {"email": "reply@example.com"})

    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    def test_send_html_message_via_content_subtype(self, mock_send):
        mock_send.return_value = SendTransacEmailResponse(message_id="<brevo_msg_002>")
        backend = BrevoEmailBackend(
            api_key="xkeysib-valid",
            from_email="support@sevabandhu.in",
        )

        msg = EmailMessage(
            subject="HTML Notice",
            body="<h1>Hello World</h1>",
            from_email="support@sevabandhu.in",
            to=["user@example.com"],
        )
        msg.content_subtype = "html"
        sent = backend.send_messages([msg])
        self.assertEqual(sent, 1)

        kwargs = mock_send.call_args[1]
        self.assertEqual(kwargs["html_content"], "<h1>Hello World</h1>")

    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    def test_send_multipart_alternative_html(self, mock_send):
        mock_send.return_value = SendTransacEmailResponse(message_id="<brevo_msg_003>")
        backend = BrevoEmailBackend(
            api_key="xkeysib-valid",
            from_email="support@sevabandhu.in",
        )

        msg = EmailMultiAlternatives(
            subject="Resolution Details",
            body="Plain text summary",
            from_email="support@sevabandhu.in",
            to=["customer@example.com"],
        )
        msg.attach_alternative("<div><p>HTML resolution</p></div>", "text/html")
        sent = backend.send_messages([msg])
        self.assertEqual(sent, 1)

        kwargs = mock_send.call_args[1]
        self.assertEqual(kwargs["text_content"], "Plain text summary")
        self.assertEqual(kwargs["html_content"], "<div><p>HTML resolution</p></div>")

    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    def test_send_with_pdf_attachment(self, mock_send):
        mock_send.return_value = SendTransacEmailResponse(message_id="<brevo_msg_004>")
        backend = BrevoEmailBackend(
            api_key="xkeysib-valid",
            from_email="billing@sevabandhu.in",
        )

        msg = EmailMessage(
            subject="Invoice #42",
            body="Invoice attached.",
            from_email="billing@sevabandhu.in",
            to=["customer@example.com"],
        )
        pdf_data = b"%PDF-1.4 test invoice binary payload"
        msg.attach("invoice_42.pdf", pdf_data, "application/pdf")

        sent = backend.send_messages([msg])
        self.assertEqual(sent, 1)

        kwargs = mock_send.call_args[1]
        self.assertIn("attachment", kwargs)
        self.assertEqual(len(kwargs["attachment"]), 1)
        att = kwargs["attachment"][0]
        self.assertEqual(att["name"], "invoice_42.pdf")
        self.assertEqual(att["content"], base64.b64encode(pdf_data).decode("utf-8"))

    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    def test_api_failure_raises_when_not_fail_silently(self, mock_send):
        mock_send.side_effect = ApiError(
            status_code=401,
            body={"code": "unauthorized", "message": "Key not found"},
        )
        backend = BrevoEmailBackend(api_key="xkeysib-invalid", fail_silently=False)
        msg = EmailMessage("Subject", "Body", "from@test.com", ["to@test.com"])

        with self.assertRaises(ApiError):
            backend.send_messages([msg])

    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    def test_api_failure_caught_when_fail_silently(self, mock_send):
        mock_send.side_effect = ApiError(
            status_code=500,
            body={"code": "internal_error", "message": "Server error"},
        )
        backend = BrevoEmailBackend(api_key="xkeysib-valid", fail_silently=True)
        msg = EmailMessage("Subject", "Body", "from@test.com", ["to@test.com"])

        sent = backend.send_messages([msg])
        self.assertEqual(sent, 0)


@override_settings(
    EMAIL_BACKEND="core.email_backend.BrevoEmailBackend",
    BREVO_API_KEY="xkeysib-mock-test-key",
    DEFAULT_FROM_EMAIL="Seva Bandhu <notifications@sevabandhu.in>",
)
class BrevoEmailIntegrationTests(TestCase):
    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    def test_django_send_mail_dispatches_to_brevo_backend(self, mock_send):
        mock_send.return_value = SendTransacEmailResponse(message_id="<brevo_mock_id_999>")

        count = send_mail(
            subject="OTP Verification",
            message="Your OTP is 123456",
            from_email="notifications@sevabandhu.in",
            recipient_list=["customer@example.com"],
            fail_silently=False,
        )
        self.assertEqual(count, 1)
        mock_send.assert_called_once()
        kwargs = mock_send.call_args[1]
        self.assertEqual(kwargs["to"], [{"email": "customer@example.com"}])
        self.assertIn("123456", kwargs["text_content"])

    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    def test_customer_verification_email_helper_calls_brevo(self, mock_send):
        mock_send.return_value = SendTransacEmailResponse(message_id="<brevo_otp_msg>")

        _send_customer_verification_email("customer_otp@example.com", "654321")

        mock_send.assert_called_once()
        kwargs = mock_send.call_args[1]
        self.assertEqual(kwargs["to"], [{"email": "customer_otp@example.com"}])
        self.assertIn("654321", kwargs["text_content"])
        self.assertEqual(kwargs["subject"], "Your Seva Bandhu verification code")

    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    def test_customer_send_verification_endpoint_calls_brevo(self, mock_send):
        mock_send.return_value = SendTransacEmailResponse(message_id="<brevo_endpoint_msg>")

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
        kwargs = mock_send.call_args[1]
        self.assertEqual(kwargs["to"], [{"email": "customer_signup_test@example.com"}])

    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    def test_technician_verification_email_dispatch(self, mock_send):
        mock_send.return_value = SendTransacEmailResponse(message_id="<brevo_tech_msg>")

        # Direct verification email test simulating technician signup flow
        token = "test-token-uuid-1234"
        verification_link = f"http://testserver/verify-email/{token}/"
        send_mail(
            subject='Verify Your Email - Seva Bandhu',
            message=f'Hi,\n\nPlease click the link below to verify your email:\n\n{verification_link}',
            from_email=None,
            recipient_list=['tech_applicant@example.com'],
            fail_silently=False,
        )

        mock_send.assert_called_once()
        kwargs = mock_send.call_args[1]
        self.assertEqual(kwargs["to"], [{"email": "tech_applicant@example.com"}])
        self.assertEqual(kwargs["subject"], "Verify Your Email - Seva Bandhu")
        self.assertIn(token, kwargs["text_content"])

    @patch("builtins.print")
    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    @patch("core.views.generate_invoice_pdf")
    def test_invoice_email_dispatch(self, mock_pdf, mock_send, mock_print):
        mock_send.return_value = SendTransacEmailResponse(message_id="<brevo_invoice_msg>")
        mock_pdf.return_value = b"%PDF-1.4 Mock Invoice Data"

        user = User.objects.create_user(username="inv_user", email="inv_user@example.com", password="password")
        cust = customer_signup.objects.create(user=user, username="inv_user", email="inv_user@example.com", contact="1234567890", password="x")

        mock_service = MagicMock()
        mock_service.id = 42
        mock_service.customer = cust

        success = send_invoice_email(mock_service)
        self.assertTrue(success)

        mock_send.assert_called_once()
        kwargs = mock_send.call_args[1]
        self.assertEqual(kwargs["to"], [{"email": "inv_user@example.com"}])
        self.assertIn("invoice", kwargs["subject"].lower())
        self.assertIn("attachment", kwargs)
        self.assertEqual(len(kwargs["attachment"]), 1)
        self.assertEqual(kwargs["attachment"][0]["name"], "invoice_42.pdf")

    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    def test_admin_support_ticket_resolution_email_dispatch(self, mock_send):
        mock_send.return_value = SendTransacEmailResponse(message_id="<brevo_support_msg>")

        user = User.objects.create_user(username="ticket_user", email="ticket_user@example.com", password="password")
        cust = customer_signup.objects.create(user=user, username="ticket_user", email="ticket_user@example.com", contact="1234567890", password="x")
        ticket = SupportTicket.objects.create(
            customer=cust,
            ticket_type="Complaint",
            description="I need help with booking.",
            status="Resolved",
        )

        subject = f"[Ticket #{ticket.id} Resolved] Help needed with booking"
        html_message = "<div><h3>Your support request has been resolved.</h3></div>"
        plain_message = "Your support request has been resolved."

        send_mail(
            subject=subject,
            message=plain_message,
            from_email="support@sevabandhu.in",
            recipient_list=[ticket.customer.email],
            html_message=html_message,
            fail_silently=False,
        )

        mock_send.assert_called_once()
        kwargs = mock_send.call_args[1]
        self.assertEqual(kwargs["to"], [{"email": "ticket_user@example.com"}])
        self.assertEqual(kwargs["subject"], subject)
        self.assertEqual(kwargs["html_content"], html_message)
        self.assertEqual(kwargs["text_content"], plain_message)
