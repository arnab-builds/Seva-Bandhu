from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import customer_signup, Technician_signup


class SupabaseAuthFlowTests(TestCase):
    def setUp(self):
        self.verify_url = reverse('supabase_auth_verify')

    def test_missing_token_or_role_returns_400(self):
        resp = self.client.post(self.verify_url, data='{}', content_type='application/json')
        self.assertEqual(resp.status_code, 400)

        resp2 = self.client.post(self.verify_url, data='{"access_token":"token"}', content_type='application/json')
        self.assertEqual(resp2.status_code, 400)

        resp3 = self.client.post(self.verify_url, data='{"access_token":"token", "role":"admin"}', content_type='application/json')
        self.assertEqual(resp3.status_code, 400)

    def test_customer_google_login_creates_and_logs_in_customer(self):
        payload = {
            'access_token': 'test_token_valid_123',
            'role': 'customer',
            'email': 'customer_google@example.com',
            'name': 'Google Customer'
        }
        resp = self.client.post(self.verify_url, data=payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['redirect_url'], '/customer/dashboard/')

        # Verify Customer record exists in DB
        cust = customer_signup.objects.filter(email='customer_google@example.com').first()
        self.assertIsNotNone(cust)
        self.assertTrue(cust.email_verified)
        self.assertEqual(int(self.client.session['_auth_user_id']), cust.user.id)

    def test_technician_google_login_creates_and_logs_in_technician(self):
        payload = {
            'access_token': 'test_token_valid_tech',
            'role': 'technician',
            'email': 'tech_google@example.com',
            'name': 'Google Technician'
        }
        resp = self.client.post(self.verify_url, data=payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['redirect_url'], '/technician/dashboard_t/')

        # Verify Technician record exists in DB
        tech = Technician_signup.objects.filter(email='tech_google@example.com').first()
        self.assertIsNotNone(tech)
        self.assertEqual(int(self.client.session['_auth_user_id']), tech.user.id)

    def test_role_contamination_prevented(self):
        # Create customer first
        customer_payload = {
            'access_token': 'test_token_dual',
            'role': 'customer',
            'email': 'shared_user@example.com',
            'name': 'Shared User'
        }
        resp = self.client.post(self.verify_url, data=customer_payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        # Attempt to sign in as technician with same customer email
        tech_payload = {
            'access_token': 'test_token_dual',
            'role': 'technician',
            'email': 'shared_user@example.com',
            'name': 'Shared User'
        }
        resp2 = self.client.post(self.verify_url, data=tech_payload, content_type='application/json')
        self.assertEqual(resp2.status_code, 403)
        self.assertIn('registered as a Customer', resp2.json()['message'])
