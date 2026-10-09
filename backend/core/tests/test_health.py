import json
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse


class HealthEndpointsTests(TestCase):
    def test_health_check_returns_200_and_ok(self):
        url = reverse('health_check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data, {'status': 'ok'})

    def test_health_check_db_returns_200_when_db_available(self):
        url = reverse('health_check_db')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data, {'status': 'ok', 'database': 'ok'})

    def test_health_check_db_returns_503_when_db_unavailable(self):
        url = reverse('health_check_db')
        with patch('django.db.connection.cursor', side_effect=Exception('DB Connection Failure')):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response['Content-Type'], 'application/json')
            data = response.json()
            self.assertEqual(data, {'status': 'error', 'database': 'unavailable'})
            # Verify no secret or stack trace is exposed in the response
            self.assertNotIn('DB Connection Failure', response.content.decode('utf-8'))

    def test_health_endpoints_reject_post_requests(self):
        r1 = self.client.post(reverse('health_check'))
        self.assertEqual(r1.status_code, 405)

        r2 = self.client.post(reverse('health_check_db'))
        self.assertEqual(r2.status_code, 405)

    def test_health_check_logging_success(self):
        url = reverse('health_check')
        user_agent = 'SevaBandhu-HealthMonitor/1.0'
        with self.assertLogs('core.health', level='INFO') as log_ctx:
            response = self.client.get(url, HTTP_USER_AGENT=user_agent)
            self.assertEqual(response.status_code, 200)

        logs = " ".join(log_ctx.output)
        self.assertIn('[HEALTH]', logs)
        self.assertIn('status=200', logs)
        self.assertIn('outcome=ok', logs)
        self.assertIn(f"user_agent='{user_agent}'", logs)

    def test_health_check_db_logging_success(self):
        url = reverse('health_check_db')
        user_agent = 'SevaBandhu-HealthMonitor/1.0'
        with self.assertLogs('core.health', level='INFO') as log_ctx:
            response = self.client.get(url, HTTP_USER_AGENT=user_agent)
            self.assertEqual(response.status_code, 200)

        logs = " ".join(log_ctx.output)
        self.assertIn('[HEALTH_DB]', logs)
        self.assertIn('status=200', logs)
        self.assertIn('db_outcome=ok', logs)
        self.assertIn(f"user_agent='{user_agent}'", logs)

    def test_health_check_db_logging_failure_no_secret_leak(self):
        url = reverse('health_check_db')
        user_agent = 'SevaBandhu-HealthMonitor/1.0'
        sensitive_error_msg = "postgres://user:supersecretpass@db.render.internal:5432/sevabandhu"
        with patch('django.db.connection.cursor', side_effect=Exception(sensitive_error_msg)):
            with self.assertLogs('core.health', level='ERROR') as log_ctx:
                response = self.client.get(url, HTTP_USER_AGENT=user_agent)
                self.assertEqual(response.status_code, 503)

        logs = " ".join(log_ctx.output)
        self.assertIn('[HEALTH_DB]', logs)
        self.assertIn('status=503', logs)
        self.assertIn('db_outcome=failed', logs)
        self.assertIn('error_type=Exception', logs)
        self.assertIn(f"user_agent='{user_agent}'", logs)
        # Verify no credentials or connection string leaked into the logs or response
        self.assertNotIn('supersecretpass', logs)
        self.assertNotIn('postgres://', logs)
        self.assertNotIn('supersecretpass', response.content.decode('utf-8'))
        self.assertNotIn('postgres://', response.content.decode('utf-8'))

    def test_health_check_logging_method_not_allowed(self):
        with self.assertLogs('core.health', level='WARNING') as log_ctx:
            r1 = self.client.post(reverse('health_check'), HTTP_USER_AGENT='TestAgent/1.0')
            self.assertEqual(r1.status_code, 405)

            r2 = self.client.post(reverse('health_check_db'), HTTP_USER_AGENT='TestAgent/1.0')
            self.assertEqual(r2.status_code, 405)

        logs = " ".join(log_ctx.output)
        self.assertIn('status=405', logs)
        self.assertIn("detail='Method not allowed'", logs)
        self.assertIn("user_agent='TestAgent/1.0'", logs)


class SettingsParsingTests(TestCase):
    def test_allowed_hosts_parsing(self):
        raw_hosts = "localhost, 127.0.0.1, example.onrender.com,   "
        parsed = [item.strip() for item in raw_hosts.split(",") if item.strip()]
        self.assertEqual(parsed, ["localhost", "127.0.0.1", "example.onrender.com"])
        self.assertNotIn("*", parsed)

    def test_debug_parsing_logic(self):
        # Case insensitive parsing rules
        def parse_debug(val, default="False"):
            return (val if val is not None else default).strip().lower() in {"1", "true", "yes", "on"}

        self.assertFalse(parse_debug("False"))
        self.assertFalse(parse_debug("false"))
        self.assertFalse(parse_debug("0"))
        self.assertFalse(parse_debug("no"))
        self.assertFalse(parse_debug(None))  # Absent environment variable defaults to False
        self.assertTrue(parse_debug("True"))
        self.assertTrue(parse_debug("true"))
        self.assertTrue(parse_debug("1"))
        self.assertTrue(parse_debug("yes"))

