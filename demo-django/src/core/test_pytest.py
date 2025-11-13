"""
Pytest-based tests for the core app.

This file demonstrates pytest testing style with Django.
Key differences from Django's unittest:
- Uses pytest fixtures instead of setUp methods
- Uses simple assert statements instead of self.assertEqual
- Uses pytest-django plugin for Django integration
- More concise and Pythonic test writing style
"""

import pytest
import json
from django.urls import reverse


# Pytest fixtures are reusable test setup functions
# The 'client' fixture is provided by pytest-django
# It's similar to Django's test client but used as a function argument


@pytest.mark.django_db
class TestHomeView:
    """Tests for the home view using pytest."""

    def test_home_view_status_code(self, client):
        """Test that home view returns 200 OK."""
        response = client.get(reverse('home'))
        assert response.status_code == 200

    def test_home_view_uses_correct_template(self, client):
        """Test that home view uses the correct template."""
        response = client.get(reverse('home'))
        # Pytest uses assertTemplateUsed via the response object
        assert 'core/home.html' in [t.name for t in response.templates]

    def test_home_view_contains_title(self, client):
        """Test that home view context contains expected title."""
        response = client.get(reverse('home'))
        assert response.context['title'] == 'Demo Django App'

    def test_home_view_contains_message(self, client):
        """Test that home view context contains expected message."""
        response = client.get(reverse('home'))
        assert 'Welcome to your homelab' in response.context['message']

    def test_home_view_content(self, client):
        """Test that home view contains expected text in HTML."""
        response = client.get(reverse('home'))
        content = response.content.decode('utf-8')
        assert 'Demo Django App' in content
        assert 'Welcome to your homelab' in content


@pytest.mark.django_db
class TestHealthView:
    """Tests for the health check endpoint."""

    def test_health_endpoint_status_code(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get(reverse('health'))
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns JSON content type."""
        response = client.get(reverse('health'))
        assert response['Content-Type'] == 'application/json'

    def test_health_endpoint_response_structure(self, client):
        """Test that health endpoint returns correct JSON structure."""
        response = client.get(reverse('health'))
        data = json.loads(response.content)
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_health_endpoint_only_allows_get(self, client):
        """Test that health endpoint only accepts GET requests."""
        response = client.post(reverse('health'))
        assert response.status_code == 405  # Method Not Allowed


@pytest.mark.django_db
class TestReadyView:
    """Tests for the readiness probe endpoint."""

    def test_ready_endpoint_status_code(self, client):
        """Test that ready endpoint returns 200 OK."""
        response = client.get(reverse('ready'))
        assert response.status_code == 200

    def test_ready_endpoint_returns_json(self, client):
        """Test that ready endpoint returns JSON content type."""
        response = client.get(reverse('ready'))
        assert response['Content-Type'] == 'application/json'

    def test_ready_endpoint_response_structure(self, client):
        """Test that ready endpoint returns correct JSON structure."""
        response = client.get(reverse('ready'))
        data = json.loads(response.content)
        assert 'status' in data
        assert data['status'] == 'ready'

    def test_ready_endpoint_only_allows_get(self, client):
        """Test that ready endpoint only accepts GET requests."""
        response = client.post(reverse('ready'))
        assert response.status_code == 405  # Method Not Allowed


@pytest.mark.django_db
class TestInfoView:
    """Tests for the system information endpoint."""

    def test_info_endpoint_status_code(self, client):
        """Test that info endpoint returns 200 OK."""
        response = client.get(reverse('info'))
        assert response.status_code == 200

    def test_info_endpoint_returns_json(self, client):
        """Test that info endpoint returns JSON content type."""
        response = client.get(reverse('info'))
        assert response['Content-Type'] == 'application/json'

    def test_info_endpoint_response_structure(self, client):
        """Test that info endpoint returns all expected fields."""
        response = client.get(reverse('info'))
        data = json.loads(response.content)

        # Check that all expected keys are present
        expected_keys = ['app', 'version', 'python_version', 'hostname', 'environment']
        for key in expected_keys:
            assert key in data

    def test_info_endpoint_app_name(self, client):
        """Test that info endpoint returns correct app name."""
        response = client.get(reverse('info'))
        data = json.loads(response.content)
        assert data['app'] == 'demo-django'

    def test_info_endpoint_version(self, client):
        """Test that info endpoint returns version."""
        response = client.get(reverse('info'))
        data = json.loads(response.content)
        assert data['version'] == '0.1.0'

    def test_info_endpoint_python_version_format(self, client):
        """Test that info endpoint returns python version in valid format."""
        response = client.get(reverse('info'))
        data = json.loads(response.content)
        # Python version should contain at least one dot (e.g., "3.11.0")
        assert '.' in data['python_version']

    def test_info_endpoint_only_allows_get(self, client):
        """Test that info endpoint only accepts GET requests."""
        response = client.post(reverse('info'))
        assert response.status_code == 405  # Method Not Allowed


# Pytest parametrize decorator allows running the same test with different inputs
@pytest.mark.django_db
@pytest.mark.parametrize("url_name,expected_path", [
    ('home', '/'),
    ('health', '/health/'),
    ('ready', '/ready/'),
    ('info', '/info/'),
])
def test_url_routing(url_name, expected_path):
    """Test that URL names resolve to correct paths."""
    url = reverse(url_name)
    assert url == expected_path


# Example of a custom fixture for reusable test data
@pytest.fixture
def json_endpoints():
    """Fixture providing list of JSON API endpoints."""
    return ['health', 'ready', 'info']


@pytest.mark.django_db
def test_all_json_endpoints_return_json(client, json_endpoints):
    """Test that all JSON endpoints return JSON content type."""
    for endpoint_name in json_endpoints:
        response = client.get(reverse(endpoint_name))
        assert response['Content-Type'] == 'application/json', \
            f"{endpoint_name} should return JSON content type"


@pytest.mark.django_db
def test_all_json_endpoints_return_200(client, json_endpoints):
    """Test that all JSON endpoints return 200 status code."""
    for endpoint_name in json_endpoints:
        response = client.get(reverse(endpoint_name))
        assert response.status_code == 200, \
            f"{endpoint_name} should return 200 status code"
