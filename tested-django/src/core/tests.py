"""
Django unittest-based tests for the core app.

This file demonstrates Django's built-in unittest framework using TestCase.
Django's TestCase is based on Python's unittest.TestCase but adds:
- Automatic database setup/teardown
- Test client for making requests
- Assertion helpers specific to Django
"""

from django.test import TestCase, Client
from django.urls import reverse
import json


class HomeViewTestCase(TestCase):
    """Tests for the home view using Django's unittest framework."""

    def setUp(self):
        """Set up test client before each test method."""
        self.client = Client()

    def test_home_view_status_code(self):
        """Test that home view returns 200 OK."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_view_uses_correct_template(self):
        """Test that home view uses the correct template."""
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'core/home.html')

    def test_home_view_contains_title(self):
        """Test that home view context contains expected title."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['title'], 'Tested Django App')

    def test_home_view_contains_message(self):
        """Test that home view context contains expected message."""
        response = self.client.get(reverse('home'))
        self.assertIn('comprehensive unit testing', response.context['message'])

    def test_home_view_content(self):
        """Test that home view contains expected text in HTML."""
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Tested Django App')
        self.assertContains(response, 'comprehensive unit testing')


class HealthViewTestCase(TestCase):
    """Tests for the health check endpoint."""

    def setUp(self):
        """Set up test client before each test method."""
        self.client = Client()

    def test_health_endpoint_status_code(self):
        """Test that health endpoint returns 200 OK."""
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 200)

    def test_health_endpoint_returns_json(self):
        """Test that health endpoint returns JSON content type."""
        response = self.client.get(reverse('health'))
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_health_endpoint_response_structure(self):
        """Test that health endpoint returns correct JSON structure."""
        response = self.client.get(reverse('health'))
        data = json.loads(response.content)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')

    def test_health_endpoint_only_allows_get(self):
        """Test that health endpoint only accepts GET requests."""
        response = self.client.post(reverse('health'))
        self.assertEqual(response.status_code, 405)  # Method Not Allowed


class ReadyViewTestCase(TestCase):
    """Tests for the readiness probe endpoint."""

    def setUp(self):
        """Set up test client before each test method."""
        self.client = Client()

    def test_ready_endpoint_status_code(self):
        """Test that ready endpoint returns 200 OK."""
        response = self.client.get(reverse('ready'))
        self.assertEqual(response.status_code, 200)

    def test_ready_endpoint_returns_json(self):
        """Test that ready endpoint returns JSON content type."""
        response = self.client.get(reverse('ready'))
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_ready_endpoint_response_structure(self):
        """Test that ready endpoint returns correct JSON structure."""
        response = self.client.get(reverse('ready'))
        data = json.loads(response.content)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'ready')

    def test_ready_endpoint_only_allows_get(self):
        """Test that ready endpoint only accepts GET requests."""
        response = self.client.post(reverse('ready'))
        self.assertEqual(response.status_code, 405)  # Method Not Allowed


class InfoViewTestCase(TestCase):
    """Tests for the system information endpoint."""

    def setUp(self):
        """Set up test client before each test method."""
        self.client = Client()

    def test_info_endpoint_status_code(self):
        """Test that info endpoint returns 200 OK."""
        response = self.client.get(reverse('info'))
        self.assertEqual(response.status_code, 200)

    def test_info_endpoint_returns_json(self):
        """Test that info endpoint returns JSON content type."""
        response = self.client.get(reverse('info'))
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_info_endpoint_response_structure(self):
        """Test that info endpoint returns all expected fields."""
        response = self.client.get(reverse('info'))
        data = json.loads(response.content)

        # Check that all expected keys are present
        expected_keys = ['app', 'version', 'python_version', 'hostname', 'environment']
        for key in expected_keys:
            self.assertIn(key, data)

    def test_info_endpoint_app_name(self):
        """Test that info endpoint returns correct app name."""
        response = self.client.get(reverse('info'))
        data = json.loads(response.content)
        self.assertEqual(data['app'], 'tested-django')

    def test_info_endpoint_version(self):
        """Test that info endpoint returns version."""
        response = self.client.get(reverse('info'))
        data = json.loads(response.content)
        self.assertEqual(data['version'], '0.1.0')

    def test_info_endpoint_python_version_format(self):
        """Test that info endpoint returns python version in valid format."""
        response = self.client.get(reverse('info'))
        data = json.loads(response.content)
        # Python version should contain at least one dot (e.g., "3.11.0")
        self.assertIn('.', data['python_version'])

    def test_info_endpoint_only_allows_get(self):
        """Test that info endpoint only accepts GET requests."""
        response = self.client.post(reverse('info'))
        self.assertEqual(response.status_code, 405)  # Method Not Allowed


class URLRoutingTestCase(TestCase):
    """Tests for URL routing and reverse URL resolution."""

    def test_home_url_resolves(self):
        """Test that home URL name resolves correctly."""
        url = reverse('home')
        self.assertEqual(url, '/')

    def test_health_url_resolves(self):
        """Test that health URL name resolves correctly."""
        url = reverse('health')
        self.assertEqual(url, '/health/')

    def test_ready_url_resolves(self):
        """Test that ready URL name resolves correctly."""
        url = reverse('ready')
        self.assertEqual(url, '/ready/')

    def test_info_url_resolves(self):
        """Test that info URL name resolves correctly."""
        url = reverse('info')
        self.assertEqual(url, '/info/')
