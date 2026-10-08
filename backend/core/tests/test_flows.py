from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import customer_signup


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class CustomerAccountFlowTests(TestCase):
    def signup(self):
        return self.client.post(reverse('customer_signup'), {
            'username': 'newcustomer', 'email': 'customer@example.com',
            'contact': '9876543210', 'password': 'StrongPass123!',
        })

    def verify_email_code(self):
        session = self.client.session
        session['verification_code_email'] = 'customer@example.com'
        session['verification_code_created_at'] = 2_000_000_000
        import hashlib
        session['verification_code_hash'] = hashlib.sha256(b'123456').hexdigest()
        session.save()
        return self.client.post(reverse('verify_email_code'), data='{"email":"customer@example.com","code":"123456"}',
                                content_type='application/json')

    def test_signup_requires_a_verified_email_code_before_creating_account(self):
        response = self.signup()
        self.assertContains(response, 'Please verify this email before signing up')
        self.assertFalse(User.objects.filter(username='newcustomer').exists())

    def test_code_verification_allows_signup_without_reentering_data(self):
        response = self.verify_email_code()
        self.assertJSONEqual(response.content, {'status': 'success', 'message': 'Email verified.'})
        response = self.signup()
        self.assertRedirects(response, reverse('customer_login'))
        user = User.objects.get(username='newcustomer')
        profile = customer_signup.objects.get(user=user)
        self.assertTrue(user.is_active)
        self.assertTrue(profile.email_verified)
        self.assertEqual(profile.password, '')

    def test_duplicate_email_is_explained_and_does_not_create_another_account(self):
        self.verify_email_code()
        self.signup()
        self.verify_email_code()
        response = self.client.post(reverse('customer_signup'), {
            'username': 'othercustomer', 'email': 'customer@example.com',
            'contact': '9876543210', 'password': 'StrongPass123!',
        })
        self.assertContains(response, 'already exists for this email')
        self.assertEqual(User.objects.filter(email='customer@example.com').count(), 1)


class TechnicianAccountFlowTests(TestCase):
    def test_technician_signup_and_login_success_and_failure(self):
        from core.models import Technician_signup

        # 1. Sign up a new technician
        signup_data = {
            'username': 'tech_pro',
            'email': 'tech_pro@example.com',
            'contact': '9876543211',
            'password': 'CorrectPassword123!',
        }
        resp = self.client.post(reverse('technician_signup'), signup_data)
        self.assertRedirects(resp, reverse('technician_login'))

        # Verify Django user and technician profile creation
        user = User.objects.get(username='tech_pro')
        tech_profile = Technician_signup.objects.get(user=user)
        self.assertEqual(tech_profile.username, 'tech_pro')
        self.assertEqual(tech_profile.email, 'tech_pro@example.com')
        self.assertEqual(tech_profile.password, '')  # Plaintext password is not stored

        # 2. Attempt login with INCORRECT password -> must fail
        bad_login_resp = self.client.post(reverse('technician_login'), {
            'username': 'tech_pro',
            'password': 'WrongPassword999!',
        })
        self.assertEqual(bad_login_resp.status_code, 200)
        self.assertContains(bad_login_resp, 'Invalid technician username or password')
        self.assertNotIn('_auth_user_id', self.client.session)

        # 3. Attempt login with CORRECT password (with whitespace in username) -> must succeed
        good_login_resp = self.client.post(reverse('technician_login'), {
            'username': '  tech_pro  ',
            'password': 'CorrectPassword123!',
        })
        self.assertRedirects(good_login_resp, reverse('technician_dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)


class RecommenderPerformanceAndOptimizationTests(TestCase):
    def setUp(self):
        from core.models import Service, ServiceDetail, ServiceAddress, ServiceRequest
        from datetime import date
        Service.objects.get_or_create(name="Plumbing", defaults={"price": 400, "is_enabled": True})
        Service.objects.get_or_create(name="Electrical", defaults={"price": 500, "is_enabled": True})
        self.user = User.objects.create_user(username="perf_user", email="perf@example.com", password="pass")
        self.cust = customer_signup.objects.create(user=self.user, username="perf_user", email="perf@example.com", contact="9876543210", password="x")

    def test_1_and_2_models_cached_and_joblib_loaded_once(self):
        from unittest.mock import patch
        import core.ml.recommender as recommender

        # Reset module state to test caching behavior
        recommender._CACHED_KNN = None
        recommender._CACHED_PIVOT = None
        recommender._MODELS_CHECKED = False

        import numpy as np
        fake_knn = type("FakeKNN", (), {"n_features_in_": 2, "kneighbors": lambda self, v, n_neighbors: (np.array([[0.1]]), np.array([[0]]))})()
        import pandas as pd
        fake_pivot = pd.DataFrame([[1, 0]], index=["perf_user"], columns=["Plumbing", "Electrical"])

        with patch("core.ml.recommender.joblib.load") as mock_load, \
             patch("os.path.exists", return_value=True):
            mock_load.side_effect = [fake_knn, fake_pivot]

            # First call triggers joblib.load
            recs1 = recommender.get_recommendations("perf_user", max_results=2)
            self.assertEqual(mock_load.call_count, 2)

            # Second call must reuse memory cache and not invoke joblib.load again
            recs2 = recommender.get_recommendations("perf_user", max_results=2)
            self.assertEqual(mock_load.call_count, 2)
            self.assertEqual(recs1, recs2)

    def test_3_recommendation_scoring_and_fallback_preserved(self):
        import core.ml.recommender as recommender
        recs = recommender.get_recommendations("perf_user", max_results=2)
        self.assertTrue(len(recs) <= 2)
        for r in recs:
            self.assertIn("service", r)
            self.assertIn("recommendation_score", r)
            self.assertIn("reason", r)

    def test_4_dashboard_technician_lookups_bulk_query_optimization(self):
        from core.models import ServiceDetail, ServiceAddress, ServiceRequest, Technician_signup
        from datetime import date
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        # Create multiple service requests with multiple technicians
        for i in range(4):
            t_user = User.objects.create_user(username=f"tech_bulk_{i}", email=f"tech_bulk_{i}@example.com", password="pass")
            Technician_signup.objects.create(user=t_user, username=f"tech_bulk_{i}", email=f"tech_bulk_{i}@example.com", contact="9876543210", password="x")
            sd = ServiceDetail.objects.create(
                service_category="Plumbing",
                problem_description="Fix leak",
                priority="Medium",
                preferred_service_date=date.today(),
                preferred_time_slot="10:00 AM - 12:00 PM",
                contact_number="9876543210"
            )
            sa = ServiceAddress.objects.create(house_flat_no="1", street_area="St", city="City", pincode="700001")
            ServiceRequest.objects.create(
                customer_username=self.cust.username,
                technician_username=f"tech_bulk_{i}",
                service_detail=sd,
                service_address=sa,
                status="Assigned"
            )

        self.client.force_login(self.user)
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse('customer_dashboard'))
            self.assertEqual(response.status_code, 200)

        # Confirm there are no N+1 individual Technician_signup queries
        tech_queries = [q['sql'] for q in ctx.captured_queries if 'Technician_signup' in q['sql']]
        # Exactly one query for Technician_signup (or at most two including session/setup)
        self.assertLessEqual(len(tech_queries), 2)

    def test_5_recommendation_logs_created_in_bulk(self):
        from core.models import RecommendationLog
        RecommendationLog.objects.filter(customer=self.cust).delete()
        self.client.force_login(self.user)
        response = self.client.get(reverse('customer_dashboard'))
        self.assertEqual(response.status_code, 200)
        logs = RecommendationLog.objects.filter(customer=self.cust)
        self.assertTrue(logs.exists())


class SecureLogoutFlowTests(TestCase):
    def setUp(self):
        from core.models import Technician_signup
        self.cust_user = User.objects.create_user(username="cust_logout_user", email="cust_lo@example.com", password="password123")
        self.cust = customer_signup.objects.create(user=self.cust_user, username="cust_logout_user", email="cust_lo@example.com", contact="9876543210", email_verified=True, password="x")

        self.tech_user = User.objects.create_user(username="tech_logout_user", email="tech_lo@example.com", password="password123")
        self.tech = Technician_signup.objects.create(user=self.tech_user, username="tech_logout_user", email="tech_lo@example.com", contact="9876543210", password="x")

    def test_6_customer_post_logout_clears_session_and_redirects(self):
        self.client.force_login(self.cust_user)
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('customer_logout'))
        self.assertRedirects(response, reverse('customer_login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_7_technician_post_logout_clears_session_and_redirects(self):
        self.client.force_login(self.tech_user)
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('technician_logout'))
        self.assertRedirects(response, reverse('technician_login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_8_get_logout_returns_405_method_not_allowed(self):
        self.client.force_login(self.cust_user)
        cust_get_resp = self.client.get(reverse('customer_logout'))
        self.assertEqual(cust_get_resp.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

        self.client.force_login(self.tech_user)
        tech_get_resp = self.client.get(reverse('technician_logout'))
        self.assertEqual(tech_get_resp.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_9_unauthenticated_dashboard_after_logout_redirects_to_login(self):
        self.client.force_login(self.cust_user)
        self.client.post(reverse('customer_logout'))
        dash_resp = self.client.get(reverse('customer_dashboard'))
        self.assertRedirects(dash_resp, reverse('customer_login'))

        self.client.force_login(self.tech_user)
        self.client.post(reverse('technician_logout'))
        tech_dash_resp = self.client.get(reverse('technician_dashboard'))
        self.assertRedirects(tech_dash_resp, reverse('technician_login'))

    def test_10_post_logout_csrf_protection_active(self):
        # Client with enforce_csrf_checks=True verifies rejection without CSRF token
        from django.test import Client
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.cust_user)
        resp = csrf_client.post(reverse('customer_logout'))
        self.assertEqual(resp.status_code, 403)

    def test_11_logout_does_not_accept_arbitrary_redirect_urls(self):
        self.client.force_login(self.cust_user)
        resp = self.client.post(reverse('customer_logout'), {'next': 'https://evil.example.com'})
        self.assertRedirects(resp, reverse('customer_login'))

    def test_12_customer_dashboard_renders_sign_out_post_form(self):
        self.client.force_login(self.cust_user)
        resp = self.client.get(reverse('customer_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, f'action="{reverse("customer_logout")}"')
        self.assertContains(resp, 'Sign Out')
        # Check cache-control headers
        self.assertIn('no-cache', resp.headers.get('Cache-Control', ''))

    def test_13_technician_dashboard_renders_sign_out_post_form(self):
        self.client.force_login(self.tech_user)
        resp = self.client.get(reverse('technician_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, f'action="{reverse("technician_logout")}"')
        self.assertContains(resp, 'Sign Out')
        # Check cache-control headers
        self.assertIn('no-cache', resp.headers.get('Cache-Control', ''))

