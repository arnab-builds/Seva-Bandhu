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

