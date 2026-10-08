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
from core.views import _send_customer_verification_email, send_invoice_email, get_customer_display_name, generate_invoice_pdf
from core.models import User, customer_signup, Technician_signup, SupportTicket, ServiceRequest, ServiceDetail, ServiceAddress


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


@override_settings(
    EMAIL_BACKEND="core.email_backend.BrevoEmailBackend",
    BREVO_API_KEY="xkeysib-mock-test-key",
    DEFAULT_FROM_EMAIL="Seva Bandhu <notifications@sevabandhu.in>",
)
class CustomerEmailIdentityTests(TestCase):
    def setUp(self):
        from datetime import date
        self.service_detail = ServiceDetail.objects.create(
            service_category="Plumbing",
            problem_description="Leaking pipe",
            priority="Medium",
            preferred_service_date=date.today(),
            preferred_time_slot="10:00 AM - 12:00 PM",
            contact_number="9876543210"
        )
        self.service_address = ServiceAddress.objects.create(
            house_flat_no="123",
            street_area="MG Road",
            city="Kolkata",
            pincode="700001"
        )

    @patch("builtins.print")
    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    @patch("core.views.generate_invoice_pdf")
    def test_1_and_9_dual_role_user_invoice_email_uses_customer_identity_and_email(self, mock_pdf, mock_send, mock_print):
        mock_send.return_value = SendTransacEmailResponse(message_id="<brevo_invoice_msg_1>")
        mock_pdf.return_value = b"%PDF-1.4 Mock Invoice"

        # User created originally as a technician
        user = User.objects.create_user(username="Ramu Singh", email="ramu@example.com", password="password123")
        tech = Technician_signup.objects.create(
            user=user,
            username="Ramu Singh",
            email="tech_ramu_work@example.com",  # Different email on tech profile
            contact="9876543210",
            password="x"
        )
        cust = customer_signup.objects.create(
            user=user,
            username="Ramu Singh",
            email="ramu_cust_fallback@example.com",
            contact="9876543210",
            password="x"
        )

        service_req = ServiceRequest.objects.create(
            customer_username=cust.username,
            service_detail=self.service_detail,
            service_address=self.service_address,
            status="Completed"
        )

        success = send_invoice_email(service_req)
        self.assertTrue(success)

        mock_send.assert_called_once()
        kwargs = mock_send.call_args[1]
        # Primary recipient is user.email, NOT tech.email
        self.assertEqual(kwargs["to"], [{"email": "ramu@example.com"}])
        # Body salutation uses resolved customer display name (Ramu Singh), not raw technician username
        self.assertIn("Hello Ramu Singh,\n\n", kwargs["text_content"])

    def test_2_customer_user_full_name_used_when_populated(self):
        user = User.objects.create_user(
            username="ramu_tech_handle",
            first_name="Ramu",
            last_name="Singh",
            email="ramu@example.com"
        )
        cust = customer_signup.objects.create(
            user=user,
            username="ramu_tech_handle",
            email="ramu@example.com",
            contact="9876543210",
            password="x"
        )
        display_name = get_customer_display_name(customer=cust)
        self.assertEqual(display_name, "Ramu Singh")

    def test_3_customer_username_used_as_fallback_when_full_name_empty(self):
        user = User.objects.create_user(
            username="cust_handle_123",
            email="handle@example.com"
        )
        cust = customer_signup.objects.create(
            user=user,
            username="cust_handle_123",
            email="handle@example.com",
            contact="9876543210",
            password="x"
        )
        display_name = get_customer_display_name(customer=cust)
        self.assertEqual(display_name, "cust_handle_123")

        # When customer has neither full_name nor username
        empty_cust = customer_signup(username="")
        self.assertEqual(get_customer_display_name(customer=empty_cust), "Valued Customer")

    def test_4_invoice_html_renders_resolved_customer_display_name(self):
        from django.template.loader import render_to_string
        service = ServiceRequest.objects.create(
            customer_username="ramu_tech_raw",
            service_detail=self.service_detail,
            service_address=self.service_address,
            status="Completed"
        )

        rendered = render_to_string("customer/invoice.html", {
            "service": service,
            "customer_display_name": "Ramu Singh"
        })
        self.assertIn("Ramu Singh", rendered)
        self.assertNotIn("ramu_tech_raw", rendered)

    @patch("builtins.print")
    def test_5_invoice_pdf_uses_resolved_customer_display_name(self, mock_print):
        user = User.objects.create_user(
            username="ramu_tech_user",
            first_name="Ramu",
            last_name="Singh",
            email="ramu@example.com"
        )
        cust = customer_signup.objects.create(
            user=user,
            username="ramu_tech_user",
            email="ramu@example.com",
            contact="9876543210",
            password="x"
        )
        service_req = ServiceRequest.objects.create(
            customer_username=cust.username,
            service_detail=self.service_detail,
            service_address=self.service_address,
            status="Completed"
        )

        pdf_bytes = generate_invoice_pdf(service_req)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(len(pdf_bytes) > 0)

    @patch("django.core.mail.send_mail")
    def test_6_support_ticket_resolution_email_prioritizes_customer_user_email(self, mock_send):
        from django.test import RequestFactory
        from core.admin_views import admin_support_ticket_action

        user = User.objects.create_user(
            username="admin_ramu",
            email="primary_user_email@example.com",
            is_staff=True,
            is_superuser=True
        )
        cust = customer_signup.objects.create(
            user=user,
            username="admin_ramu",
            email="stale_cust_email@example.com",
            contact="9876543210",
            password="x"
        )
        ticket = SupportTicket.objects.create(
            customer=cust,
            ticket_type="Complaint",
            description="Service issue",
            status="Open"
        )

        rf = RequestFactory()
        post_data = {
            'status': 'Resolved',
            'action_notes': 'Issue resolved successfully.',
            'resolution_type': 'Issue Resolved (Standard)',
            'send_email': 'on'
        }
        request = rf.post(f"/admin/support-tickets/{ticket.id}/action/", post_data)
        request.user = user

        # Add message middleware support
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))

        response = admin_support_ticket_action(request, ticket.id)
        self.assertEqual(response.status_code, 302)

        mock_send.assert_called_once()
        recipient_list = mock_send.call_args[0][3]
        self.assertEqual(recipient_list, ["primary_user_email@example.com"])

    @patch("builtins.print")
    @patch("brevo.transactional_emails.client.TransactionalEmailsClient.send_transac_email")
    @patch("core.views.generate_invoice_pdf")
    def test_7_existing_single_role_customer_invoice_email_works(self, mock_pdf, mock_send, mock_print):
        mock_send.return_value = SendTransacEmailResponse(message_id="<brevo_invoice_single_cust>")
        mock_pdf.return_value = b"%PDF-1.4 Mock Single Customer"

        user = User.objects.create_user(username="single_customer", email="single_cust@example.com", password="password")
        cust = customer_signup.objects.create(user=user, username="single_customer", email="single_cust@example.com", contact="9876543210", password="x")
        service_req = ServiceRequest.objects.create(
            customer_username=cust.username,
            service_detail=self.service_detail,
            service_address=self.service_address,
            status="Completed"
        )

        success = send_invoice_email(service_req)
        self.assertTrue(success)
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args[1]["to"], [{"email": "single_cust@example.com"}])
        self.assertIn("Hello single_customer,\n\n", mock_send.call_args[1]["text_content"])

    def test_8_existing_technician_only_behavior_is_unchanged(self):
        user = User.objects.create_user(username="solo_tech", email="solo_tech@example.com", password="password")
        tech = Technician_signup.objects.create(
            user=user,
            username="solo_tech",
            email="solo_tech@example.com",
            contact="9876543210",
            password="x"
        )
        self.assertEqual(tech.user.email, "solo_tech@example.com")
        self.assertFalse(customer_signup.objects.filter(user=user).exists())

