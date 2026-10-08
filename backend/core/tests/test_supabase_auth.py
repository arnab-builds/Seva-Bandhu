from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import customer_signup, Technician_signup


class SupabaseAuthFlowTests(TestCase):
    def setUp(self):
        self.verify_url = reverse('supabase_auth_verify')
        self.complete_profile_url = reverse('complete_google_profile')

    def test_missing_token_or_role_returns_400(self):
        resp = self.client.post(self.verify_url, data='{}', content_type='application/json')
        self.assertEqual(resp.status_code, 400)

        resp2 = self.client.post(self.verify_url, data='{"access_token":"token"}', content_type='application/json')
        self.assertEqual(resp2.status_code, 400)

        resp3 = self.client.post(self.verify_url, data='{"access_token":"token", "role":"admin"}', content_type='application/json')
        self.assertEqual(resp3.status_code, 400)

    # A. New Google Customer:
    # Google -> complete profile -> mobile saved -> customer dashboard
    def test_new_customer_google_user_redirects_to_complete_profile_and_saves_mobile(self):
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
        self.assertEqual(data['redirect_url'], '/auth/complete-profile/?next=customer')

        # Verify Customer record exists with empty contact and phone_verified=False
        cust = customer_signup.objects.filter(email='new_customer@example.com').first()
        self.assertIsNotNone(cust)
        self.assertTrue(cust.email_verified)
        self.assertFalse(cust.phone_verified)
        self.assertEqual(cust.contact, '')
        self.assertEqual(int(self.client.session['_auth_user_id']), cust.user.id)
        self.assertEqual(User.objects.filter(email='new_customer@example.com').count(), 1)

        # GET complete profile page works
        get_resp = self.client.get(self.complete_profile_url + '?next=customer')
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, 'Complete Your Profile')
        self.assertContains(get_resp, 'Your mobile number is required for service-related communication.')
        self.assertNotContains(get_resp, 'verified')

        # POST valid mobile number
        post_resp = self.client.post(self.complete_profile_url, {'mobile': '9876543210', 'next': 'customer'})
        self.assertRedirects(post_resp, reverse('customer_dashboard'))

        cust.refresh_from_db()
        self.assertEqual(cust.contact, '9876543210')
        self.assertFalse(cust.phone_verified)

    # B. New Google Technician:
    # Google -> complete profile -> mobile saved -> technician dashboard
    def test_new_technician_google_user_redirects_to_complete_profile_and_saves_mobile(self):
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
        self.assertEqual(data['redirect_url'], '/auth/complete-profile/?next=technician')

        tech = Technician_signup.objects.filter(email='new_tech@example.com').first()
        self.assertIsNotNone(tech)
        self.assertEqual(tech.contact, '')
        self.assertEqual(int(self.client.session['_auth_user_id']), tech.user.id)
        self.assertEqual(User.objects.filter(email='new_tech@example.com').count(), 1)

        # POST valid mobile number
        post_resp = self.client.post(self.complete_profile_url, {'mobile': '9876543211', 'next': 'technician'})
        self.assertRedirects(post_resp, reverse('technician_dashboard'))

        tech.refresh_from_db()
        self.assertEqual(tech.contact, '9876543211')

    # C. Existing Customer with mobile:
    # Google Customer login -> directly customer dashboard
    def test_existing_customer_with_mobile_goes_directly_to_dashboard(self):
        user = User.objects.create_user(
            username='existing_cust',
            email='existing_cust@example.com',
            password='CustomerPassword789!'
        )
        cust = customer_signup.objects.create(
            user=user,
            username='existing_cust',
            email='existing_cust@example.com',
            contact='9876543212',
            email_verified=False,
            phone_verified=False
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
        self.assertFalse(cust.phone_verified)
        self.assertEqual(cust.contact, '9876543212')
        self.assertEqual(customer_signup.objects.filter(email='existing_cust@example.com').count(), 1)
        self.assertEqual(User.objects.filter(email='existing_cust@example.com').count(), 1)

    # D. Existing Technician with mobile:
    # Google Technician login -> directly technician dashboard
    def test_existing_technician_with_mobile_goes_directly_to_dashboard(self):
        user = User.objects.create_user(
            username='existing_tech',
            email='existing_tech@example.com',
            password='TraditionalPassword456!'
        )
        tech = Technician_signup.objects.create(
            user=user,
            username='existing_tech',
            email='existing_tech@example.com',
            contact='9876543213'
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

    # E. Existing Technician without mobile:
    # Google Customer login -> complete profile -> save mobile -> customer dashboard
    def test_existing_technician_without_mobile_creating_customer_profile(self):
        user = User.objects.create_user(
            username='tech_nomobile',
            email='tech_nomobile@example.com',
            password='TechPassword123!'
        )
        tech = Technician_signup.objects.create(
            user=user,
            username='tech_nomobile',
            email='tech_nomobile@example.com',
            contact=''
        )
        initial_hash = user.password

        cust_payload = {
            'access_token': 'test_token_cust_on_tech_nomobile',
            'role': 'customer',
            'email': 'tech_nomobile@example.com',
            'name': 'Tech Nomobile'
        }
        resp = self.client.post(self.verify_url, data=cust_payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['redirect_url'], '/auth/complete-profile/?next=customer')

        # Submit mobile on complete profile
        post_resp = self.client.post(self.complete_profile_url, {'mobile': '9876543214', 'next': 'customer'})
        self.assertRedirects(post_resp, reverse('customer_dashboard'))

        # Both profiles have the mobile updated
        cust = customer_signup.objects.filter(email='tech_nomobile@example.com').first()
        tech.refresh_from_db()
        self.assertEqual(cust.contact, '9876543214')
        self.assertEqual(tech.contact, '9876543214')
        self.assertFalse(cust.phone_verified)
        self.assertEqual(User.objects.filter(email='tech_nomobile@example.com').count(), 1)

        user.refresh_from_db()
        self.assertEqual(user.password, initial_hash)

    # F. Existing Customer without mobile:
    # Google Technician login -> complete profile -> save mobile -> technician dashboard
    def test_existing_customer_without_mobile_creating_technician_profile(self):
        user = User.objects.create_user(
            username='cust_nomobile',
            email='cust_nomobile@example.com',
            password='CustPassword123!'
        )
        cust = customer_signup.objects.create(
            user=user,
            username='cust_nomobile',
            email='cust_nomobile@example.com',
            contact='',
            phone_verified=False
        )
        initial_hash = user.password

        tech_payload = {
            'access_token': 'test_token_tech_on_cust_nomobile',
            'role': 'technician',
            'email': 'cust_nomobile@example.com',
            'name': 'Cust Nomobile'
        }
        resp = self.client.post(self.verify_url, data=tech_payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['redirect_url'], '/auth/complete-profile/?next=technician')

        post_resp = self.client.post(self.complete_profile_url, {'mobile': '9876543215', 'next': 'technician'})
        self.assertRedirects(post_resp, reverse('technician_dashboard'))

        tech = Technician_signup.objects.filter(email='cust_nomobile@example.com').first()
        cust.refresh_from_db()
        self.assertEqual(cust.contact, '9876543215')
        self.assertEqual(tech.contact, '9876543215')
        self.assertFalse(cust.phone_verified)
        self.assertEqual(User.objects.filter(email='cust_nomobile@example.com').count(), 1)

        user.refresh_from_db()
        self.assertEqual(user.password, initial_hash)

    # G. Existing user with BOTH profiles and mobile:
    # Customer Google login -> customer dashboard.
    # Technician Google login -> technician dashboard.
    # No profile completion page.
    def test_existing_user_with_both_profiles_and_mobile_direct_dashboards(self):
        user = User.objects.create_user(
            username='dual_with_mobile',
            email='dual_with_mobile@example.com',
            password='DualPassword123!'
        )
        customer_signup.objects.create(
            user=user,
            username='dual_with_mobile',
            email='dual_with_mobile@example.com',
            contact='9876543216',
            phone_verified=False
        )
        Technician_signup.objects.create(
            user=user,
            username='dual_with_mobile',
            email='dual_with_mobile@example.com',
            contact='9876543216'
        )
        original_hash = user.password

        # Customer login
        resp1 = self.client.post(self.verify_url, data={
            'access_token': 'test_token_dual_c',
            'role': 'customer',
            'email': 'dual_with_mobile@example.com'
        }, content_type='application/json')
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.json()['redirect_url'], '/customer/dashboard/')

        # Technician login
        resp2 = self.client.post(self.verify_url, data={
            'access_token': 'test_token_dual_t',
            'role': 'technician',
            'email': 'dual_with_mobile@example.com'
        }, content_type='application/json')
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()['redirect_url'], '/technician/dashboard_t/')

        self.assertEqual(User.objects.filter(email='dual_with_mobile@example.com').count(), 1)
        user.refresh_from_db()
        self.assertEqual(user.password, original_hash)

    # H. Existing user with BOTH profiles but no mobile:
    # Either role -> complete profile -> save one mobile number to both profiles -> requested role dashboard.
    def test_existing_user_with_both_profiles_no_mobile_updates_both_profiles(self):
        user = User.objects.create_user(
            username='dual_nomobile',
            email='dual_nomobile@example.com',
            password='DualPassword456!'
        )
        cust = customer_signup.objects.create(
            user=user,
            username='dual_nomobile',
            email='dual_nomobile@example.com',
            contact='',
            phone_verified=False
        )
        tech = Technician_signup.objects.create(
            user=user,
            username='dual_nomobile',
            email='dual_nomobile@example.com',
            contact=''
        )

        resp = self.client.post(self.verify_url, data={
            'access_token': 'test_token_dual_nomobile',
            'role': 'technician',
            'email': 'dual_nomobile@example.com'
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['redirect_url'], '/auth/complete-profile/?next=technician')

        post_resp = self.client.post(self.complete_profile_url, {'mobile': '9876543217', 'next': 'technician'})
        self.assertRedirects(post_resp, reverse('technician_dashboard'))

        cust.refresh_from_db()
        tech.refresh_from_db()
        self.assertEqual(cust.contact, '9876543217')
        self.assertEqual(tech.contact, '9876543217')
        self.assertFalse(cust.phone_verified)

    # I. Invalid mobile:
    # Reject letters, fewer than 10 digits, more than 10 digits, and numbers beginning with 0-5.
    def test_invalid_mobile_rejected(self):
        user = User.objects.create_user(username='validator_user', email='validator@example.com')
        customer_signup.objects.create(user=user, username='validator_user', email='validator@example.com', contact='')
        self.client.force_login(user)

        invalid_numbers = [
            '1234567890',     # starts with 1
            '5555555555',     # starts with 5
            '0987654321',     # starts with 0
            '98765',          # fewer than 10 digits
            '987654321012',   # more than 10 digits
            '98765abcde',     # letters
            '98765 4321',     # whitespace
        ]

        for num in invalid_numbers:
            resp = self.client.post(self.complete_profile_url, {'mobile': num, 'next': 'customer'})
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, 'Please enter a valid 10-digit Indian mobile number')
            cust = customer_signup.objects.get(user=user)
            self.assertEqual(cust.contact, '')

    # J. Unauthenticated access & Arbitrary redirect prevention
    def test_unauthenticated_access_and_arbitrary_redirect_prevention(self):
        # Unauthenticated GET/POST redirects to login
        get_resp = self.client.get(self.complete_profile_url)
        self.assertEqual(get_resp.status_code, 302)
        self.assertIn('/accounts/login/', get_resp.url) or self.assertIn('/login/', get_resp.url)

        post_resp = self.client.post(self.complete_profile_url, {'mobile': '9876543210'})
        self.assertEqual(post_resp.status_code, 302)

        # Authenticated user trying to supply arbitrary external URL
        user = User.objects.create_user(username='sec_user', email='sec@example.com')
        customer_signup.objects.create(user=user, username='sec_user', email='sec@example.com', contact='')
        self.client.force_login(user)

        # Malicious redirect in next parameter is ignored, safely falling back to customer dashboard
        safe_resp = self.client.post(self.complete_profile_url, {'mobile': '9876543218', 'next': 'https://evil.com'})
        self.assertRedirects(safe_resp, reverse('customer_dashboard'))
