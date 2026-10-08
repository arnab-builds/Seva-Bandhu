from django.contrib.auth.models import User
from django.test import TestCase
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

    # 1. New Customer Google user
    def test_new_customer_google_user_creates_account_and_logs_in(self):
        payload = {
            'access_token': 'test_token_new_cust',
            'role': 'customer',
            'email': 'new_customer@example.com',
            'name': 'New Customer'
        }
        resp = self.client.post(self.verify_url, data=payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['redirect_url'], '/customer/dashboard/')

        # Verify Customer record exists in DB
        cust = customer_signup.objects.filter(email='new_customer@example.com').first()
        self.assertIsNotNone(cust)
        self.assertTrue(cust.email_verified)
        self.assertTrue(cust.phone_verified)
        self.assertEqual(int(self.client.session['_auth_user_id']), cust.user.id)
        # Verify exactly 1 user
        self.assertEqual(User.objects.filter(email='new_customer@example.com').count(), 1)

    # 2. Existing Customer Google user
    def test_existing_customer_google_user_authenticates_and_preserves_password(self):
        user = User.objects.create_user(
            username='existing_cust',
            email='existing_cust@example.com',
            password='CustomerPassword789!'
        )
        cust = customer_signup.objects.create(
            user=user,
            username='existing_cust',
            email='existing_cust@example.com',
            contact='1112223334',
            email_verified=False
        )
        original_password_hash = user.password

        payload = {
            'access_token': 'test_token_existing_cust',
            'role': 'customer',
            'email': 'existing_cust@example.com',
            'name': 'Existing Customer'
        }
        resp = self.client.post(self.verify_url, data=payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['redirect_url'], '/customer/dashboard/')

        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

        user.refresh_from_db()
        self.assertEqual(user.password, original_password_hash)
        self.assertTrue(user.check_password('CustomerPassword789!'))

        cust.refresh_from_db()
        self.assertTrue(cust.email_verified)
        self.assertEqual(customer_signup.objects.filter(email='existing_cust@example.com').count(), 1)
        self.assertEqual(User.objects.filter(email='existing_cust@example.com').count(), 1)

    # 3. New Technician Google user
    def test_new_technician_google_user_creates_account_and_logs_in(self):
        payload = {
            'access_token': 'test_token_new_tech',
            'role': 'technician',
            'email': 'new_tech@example.com',
            'name': 'New Tech'
        }
        resp = self.client.post(self.verify_url, data=payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['redirect_url'], '/technician/dashboard_t/')

        # Verify Technician record exists in DB
        tech = Technician_signup.objects.filter(email='new_tech@example.com').first()
        self.assertIsNotNone(tech)
        self.assertEqual(int(self.client.session['_auth_user_id']), tech.user.id)
        # Verify exactly 1 user
        self.assertEqual(User.objects.filter(email='new_tech@example.com').count(), 1)

    # 4. Existing Technician Google user
    def test_existing_technician_google_user_authenticates_and_preserves_password(self):
        user = User.objects.create_user(
            username='existing_tech',
            email='existing_tech@example.com',
            password='TraditionalPassword456!'
        )
        tech = Technician_signup.objects.create(
            user=user,
            username='existing_tech',
            email='existing_tech@example.com',
            contact='9998887776'
        )
        original_password_hash = user.password

        payload = {
            'access_token': 'test_token_existing_tech',
            'role': 'technician',
            'email': 'existing_tech@example.com',
            'name': 'Existing Tech'
        }
        resp = self.client.post(self.verify_url, data=payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['redirect_url'], '/technician/dashboard_t/')

        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

        user.refresh_from_db()
        self.assertEqual(user.password, original_password_hash)
        self.assertTrue(user.check_password('TraditionalPassword456!'))

        self.assertEqual(Technician_signup.objects.filter(email='existing_tech@example.com').count(), 1)
        self.assertEqual(User.objects.filter(email='existing_tech@example.com').count(), 1)

    # 5. Existing Technician + new Customer profile using the same email
    def test_existing_technician_creates_new_customer_profile_same_email(self):
        user = User.objects.create_user(
            username='tech_first',
            email='tech_first@example.com',
            password='TechInitialPass123!'
        )
        tech = Technician_signup.objects.create(
            user=user,
            username='tech_first',
            email='tech_first@example.com',
            contact='9988776655'
        )
        initial_hash = user.password

        # Log in via Google as Customer
        cust_payload = {
            'access_token': 'test_token_cust_on_tech',
            'role': 'customer',
            'email': 'tech_first@example.com',
            'name': 'Tech First'
        }
        resp = self.client.post(self.verify_url, data=cust_payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['redirect_url'], '/customer/dashboard/')

        # Both profiles exist, linked to same Django user
        cust = customer_signup.objects.filter(email='tech_first@example.com').first()
        self.assertIsNotNone(cust)
        self.assertEqual(cust.user.id, user.id)
        self.assertEqual(tech.user.id, user.id)

        # No duplicate user created
        self.assertEqual(User.objects.filter(email='tech_first@example.com').count(), 1)

        # Password hash unchanged
        user.refresh_from_db()
        self.assertEqual(user.password, initial_hash)

    # 6. Existing Customer + new Technician profile using the same email
    def test_existing_customer_creates_new_technician_profile_same_email(self):
        user = User.objects.create_user(
            username='cust_first',
            email='cust_first@example.com',
            password='CustInitialPass123!'
        )
        cust = customer_signup.objects.create(
            user=user,
            username='cust_first',
            email='cust_first@example.com',
            contact='1122334455'
        )
        initial_hash = user.password

        # Log in via Google as Technician
        tech_payload = {
            'access_token': 'test_token_tech_on_cust',
            'role': 'technician',
            'email': 'cust_first@example.com',
            'name': 'Cust First'
        }
        resp = self.client.post(self.verify_url, data=tech_payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['redirect_url'], '/technician/dashboard_t/')

        # Both profiles exist, linked to same Django user
        tech = Technician_signup.objects.filter(email='cust_first@example.com').first()
        self.assertIsNotNone(tech)
        self.assertEqual(tech.user.id, user.id)
        self.assertEqual(cust.user.id, user.id)

        # No duplicate user created
        self.assertEqual(User.objects.filter(email='cust_first@example.com').count(), 1)

        # Password hash unchanged
        user.refresh_from_db()
        self.assertEqual(user.password, initial_hash)

    # 7. User with both profiles can authenticate as either role
    # 8. No duplicate Django User is created
    # 9. Existing password hash remains unchanged
    def test_user_with_both_profiles_can_authenticate_as_either_role(self):
        user = User.objects.create_user(
            username='dual_user',
            email='dual_user@example.com',
            password='DualRolePass123!'
        )
        customer_signup.objects.create(
            user=user,
            username='dual_user',
            email='dual_user@example.com',
            contact='1234567890'
        )
        Technician_signup.objects.create(
            user=user,
            username='dual_user',
            email='dual_user@example.com',
            contact='0987654321'
        )
        original_hash = user.password

        # 1. Authenticate as Customer
        cust_payload = {
            'access_token': 'test_token_dual_cust',
            'role': 'customer',
            'email': 'dual_user@example.com',
            'name': 'Dual User'
        }
        resp1 = self.client.post(self.verify_url, data=cust_payload, content_type='application/json')
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.json()['redirect_url'], '/customer/dashboard/')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

        # 2. Authenticate as Technician
        tech_payload = {
            'access_token': 'test_token_dual_tech',
            'role': 'technician',
            'email': 'dual_user@example.com',
            'name': 'Dual User'
        }
        resp2 = self.client.post(self.verify_url, data=tech_payload, content_type='application/json')
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()['redirect_url'], '/technician/dashboard_t/')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

        # Confirm no duplicate User created
        self.assertEqual(User.objects.filter(email='dual_user@example.com').count(), 1)

        # Confirm password hash remains untouched
        user.refresh_from_db()
        self.assertEqual(user.password, original_hash)
        self.assertTrue(user.check_password('DualRolePass123!'))
