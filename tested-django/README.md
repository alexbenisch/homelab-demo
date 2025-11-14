# Tested Django - Comprehensive Unit Testing Example

A Django application demonstrating Django's integrated unit testing framework with automated CI/CD testing in GitHub Actions. This project showcases best practices for testing Django applications and deploying them to Kubernetes with confidence.

## Overview

This application serves as a practical example of:
- **Django's built-in unittest framework** for comprehensive test coverage
- **GitHub Actions CI/CD** with automated testing before deployment
- **Test-driven development** (TDD) practices
- **Production-ready deployment** only after tests pass

## Features

- **Comprehensive Test Suite**: Full test coverage using Django's TestCase
- **Automated CI/CD**: GitHub Actions workflow that runs tests before building
- **Django's unittest framework**: Using Django's native testing tools
- **PostgreSQL Database**: Production-ready database with persistent storage
- **Health Probes**: Kubernetes liveness and readiness endpoints
- **Production-Ready**: Gunicorn WSGI server with WhiteNoise for static files

## Live Demo

Once deployed:
- **URL**: `https://tested-django.k8s-demo.de`
- **Admin**: `https://tested-django.k8s-demo.de/admin/`
- **Health**: `https://tested-django.k8s-demo.de/health/`
- **Info**: `https://tested-django.k8s-demo.de/info/`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Home page with app information |
| `GET /health/` | Health check (liveness probe) |
| `GET /ready/` | Readiness check |
| `GET /info/` | System and environment information |
| `GET /admin/` | Django admin interface |

## Test Suite

The application includes comprehensive tests covering:

### HomeViewTestCase
- Status code validation
- Template usage verification
- Context data validation
- HTML content verification

### HealthViewTestCase
- Status code validation
- JSON content type verification
- Response structure validation
- HTTP method restrictions

### ReadyViewTestCase
- Readiness probe functionality
- JSON response validation
- HTTP method restrictions

### InfoViewTestCase
- System information endpoint testing
- Response field validation
- Data format verification
- App metadata validation

### URLRoutingTestCase
- URL pattern resolution
- Reverse URL lookup verification

## Running Tests Locally

### Prerequisites

- Python 3.11+
- [uv package manager](https://github.com/astral-sh/uv) (recommended)

### Setup and Run Tests

```bash
# Navigate to the tested-django directory
cd tested-django

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
# OR with uv:
uv sync

# Navigate to src directory
cd src

# Run Django's built-in unittest
python manage.py test

# Run with verbose output
python manage.py test --verbosity=2

# Run specific test class
python manage.py test core.tests.HealthViewTestCase

# Run specific test method
python manage.py test core.tests.HealthViewTestCase.test_health_endpoint_status_code
```

## CI/CD Workflow

The GitHub Actions workflow (`.github/workflows/tested-django.yaml`) implements a comprehensive testing pipeline:

### Test Job
1. **Checkout code** from repository
2. **Set up Python 3.11** environment
3. **Install dependencies** using uv
4. **Run Django unittest tests** with verbose output (`manage.py test`)

### Build and Push Job
1. **Only runs if tests pass** (needs: test)
2. **Build Docker image** with multi-stage build
3. **Push to GitHub Container Registry** (ghcr.io)
4. **Tag with commit SHA and latest**
5. **Use build cache** for faster builds

## Local Development

### Setup

```bash
# Navigate to the tested-django directory
cd tested-django

# Create virtual environment
uv sync

# Navigate to src directory
cd src

# Run migrations
python manage.py migrate

# Create superuser (for admin access)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver
```

The app will be available at `http://localhost:8000`

### Using Docker Locally

```bash
# Build the Docker image
cd tested-django
docker build -t tested-django:dev .

# Run the container
docker run -p 8000:8000 \
  -e DJANGO_SECRET_KEY=local-dev-secret \
  -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
  -e DJANGO_DEBUG=True \
  tested-django:dev
```

## Test-Driven Development Workflow

This project demonstrates TDD practices:

### 1. Write Tests First

```python
# src/core/tests.py
class NewFeatureTestCase(TestCase):
    def test_new_feature_returns_success(self):
        response = self.client.get(reverse('new-feature'))
        self.assertEqual(response.status_code, 200)
```

### 2. Run Tests (They Should Fail)

```bash
python manage.py test core.tests.NewFeatureTestCase
# Expected: FAILED (no such URL pattern)
```

### 3. Implement the Feature

```python
# src/core/views.py
def new_feature(request):
    return JsonResponse({'status': 'success'})

# src/core/urls.py
urlpatterns = [
    # ...
    path('new-feature/', views.new_feature, name='new-feature'),
]
```

### 4. Run Tests Again (They Should Pass)

```bash
python manage.py test core.tests.NewFeatureTestCase
# Expected: OK
```

### 5. Commit and Push

```bash
git add .
git commit -m "Add new feature with tests"
git push origin main
# GitHub Actions will run all tests automatically
```

## PostgreSQL Database

### Architecture

The deployment includes a dedicated PostgreSQL database:

- **PostgreSQL 16 Alpine**: Lightweight, production-ready database
- **Persistent Storage**: 5Gi PersistentVolumeClaim for data persistence
- **Health Checks**: Liveness and readiness probes using `pg_isready`
- **Resource Limits**: CPU and memory limits for stability
- **Secure Configuration**: Credentials stored in SOPS-encrypted secrets

### Database Schema

The PostgreSQL database includes Django's default tables plus any custom models:

```bash
# View database tables
kubectl exec -n tested-django deployment/postgres -- \
  psql -U tested_django -d tested_django -c '\dt'

# View database connections
kubectl exec -n tested-django deployment/postgres -- \
  psql -U tested_django -d tested_django -c 'SELECT * FROM pg_stat_activity;'
```

### Backup and Restore

```bash
# Backup database
kubectl exec -n tested-django deployment/postgres -- \
  pg_dump -U tested_django tested_django > backup.sql

# Restore database
kubectl exec -i -n tested-django deployment/postgres -- \
  psql -U tested_django tested_django < backup.sql
```

## Deployment Workflow

### 1. Code Changes

Make changes to the Django application:

```bash
cd tested-django/src/core
# Edit views.py, tests.py, etc.
git add .
git commit -m "Add new feature with comprehensive tests"
git push origin main
```

### 2. Automated Testing (GitHub Actions)

GitHub Actions automatically:
1. Runs all Django unittest tests
2. Runs pytest with coverage
3. **Blocks deployment if tests fail**
4. Only proceeds to build if all tests pass

### 3. Automated Build (After Tests Pass)

If tests pass, GitHub Actions:
1. Builds the Docker image
2. Pushes to GitHub Container Registry
3. Tags with commit SHA and latest

### 4. Automated Deployment (Flux CD)

Flux CD:
1. Detects changes in Kubernetes manifests
2. Applies updates to the cluster
3. Pulls the new tested image
4. Performs rolling updates

### 5. Verification

```bash
# Check Flux status
flux get kustomizations

# Check pod status
kubectl get pods -n tested-django

# View logs
kubectl logs -n tested-django -l app=tested-django -f

# Check rollout status
kubectl rollout status deployment/tested-django -n tested-django
```

## Understanding Django's Test Framework

### TestCase vs SimpleTestCase

```python
# Use TestCase when you need database access
class MyModelTest(TestCase):
    def test_model_creation(self):
        obj = MyModel.objects.create(name="test")
        self.assertEqual(obj.name, "test")

# Use SimpleTestCase for tests without database
class MyUtilTest(SimpleTestCase):
    def test_utility_function(self):
        result = my_utility_function()
        self.assertTrue(result)
```

### Test Client Usage

```python
# Making GET requests
response = self.client.get('/api/endpoint/')
self.assertEqual(response.status_code, 200)

# Making POST requests with data
response = self.client.post('/api/create/', {
    'name': 'test',
    'value': 42
})

# Checking response content
self.assertContains(response, 'expected text')
self.assertJSONEqual(response.content, {'key': 'value'})
```

### Common Assertions

```python
# Status codes
self.assertEqual(response.status_code, 200)
self.assertEqual(response.status_code, 404)

# Templates
self.assertTemplateUsed(response, 'my_template.html')

# Context
self.assertIn('key', response.context)
self.assertEqual(response.context['key'], 'value')

# Content
self.assertContains(response, 'text')
self.assertNotContains(response, 'text')

# Redirects
self.assertRedirects(response, '/expected/url/')

# Forms
self.assertFormError(response, 'form', 'field', 'error')
```

## CI/CD Best Practices Demonstrated

1. **Test Before Build**: Tests run before building the Docker image
2. **Fail Fast**: Build is blocked if any test fails
3. **Coverage Tracking**: Monitor test coverage over time
4. **Verbose Output**: Detailed test results in CI logs
5. **Multiple Test Runners**: Both unittest and pytest for flexibility
6. **Automated Deployment**: Only tested code reaches production

## Adding New Tests

When adding new features, always add tests:

```python
# src/core/tests.py
class MyNewFeatureTestCase(TestCase):
    """Tests for my new feature."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()

    def test_feature_works(self):
        """Test that the feature works as expected."""
        response = self.client.get(reverse('my-feature'))
        self.assertEqual(response.status_code, 200)

    def test_feature_handles_errors(self):
        """Test error handling."""
        response = self.client.get(reverse('my-feature'), {'invalid': 'data'})
        self.assertEqual(response.status_code, 400)
```

## Monitoring Test Results

### In GitHub Actions

1. Go to the **Actions** tab in your repository
2. Select the **Build and Push Tested Django** workflow
3. View test output in the **test** job
4. Review detailed test results with verbosity level 2

### Locally

```bash
# Run tests with verbose output
python manage.py test --verbosity=2

# Run tests and see detailed failure information
python manage.py test --verbosity=3
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | From secret | Django secret key (encrypted with SOPS) |
| `DJANGO_ALLOWED_HOSTS` | `tested-django.k8s-demo.de,...` | Allowed hostnames |
| `DJANGO_DEBUG` | `False` | Debug mode (always False in production) |
| `ENVIRONMENT` | `production` | Environment name |
| `POSTGRES_HOST` | - | PostgreSQL host (presence triggers PostgreSQL mode) |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `tested_django` | PostgreSQL database name |
| `POSTGRES_USER` | From secret | PostgreSQL username |
| `POSTGRES_PASSWORD` | From secret | PostgreSQL password |

### Database Configuration

The application uses **PostgreSQL in production** (Kubernetes) and **SQLite for local development**:

- **Production**: When `POSTGRES_HOST` environment variable is set, Django connects to PostgreSQL
- **Local Development**: Without `POSTGRES_HOST`, Django uses SQLite (no additional setup needed)

This allows for seamless local development without requiring PostgreSQL installation.

### Secrets Management

```bash
# Generate a new secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Edit the secret
vim apps/base/tested-django/secret.yaml

# Encrypt with SOPS
sops -e -i apps/base/tested-django/secret.yaml

# Commit and push
git add apps/base/tested-django/secret.yaml
git commit -m "Update Django secret key"
git push
```

## Troubleshooting

### Tests Fail Locally

```bash
# Check for missing dependencies
uv sync

# Run with verbose output
python manage.py test --verbosity=2

# Run specific failing test
python manage.py test core.tests.HealthViewTestCase.test_health_endpoint_status_code
```

### Tests Pass Locally but Fail in CI

```bash
# Check Python version matches CI
python --version  # Should be 3.11+

# Ensure clean environment
rm -rf .venv
uv sync
python manage.py test
```

### Deployment Blocked by Failed Tests

1. Check GitHub Actions workflow logs
2. Identify failing tests
3. Fix the tests or the code
4. Push the fix
5. GitHub Actions will re-run automatically

## Resources

- [Django Testing Documentation](https://docs.djangoproject.com/en/5.0/topics/testing/)
- [Django TestCase API](https://docs.djangoproject.com/en/5.0/topics/testing/tools/)
- [Django Unittest Assertions](https://docs.djangoproject.com/en/5.0/topics/testing/tools/#assertions)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Test-Driven Development Guide](https://testdriven.io/)

## Next Steps

### Enhance Test Coverage

- Add integration tests
- Test database interactions
- Test form validation
- Test authentication and permissions

### Add Advanced Testing Features

- Use Django test fixtures for complex data
- Create test factories for model instances
- Mock external dependencies with unittest.mock
- Add performance and load testing

### Improve CI/CD Pipeline

- Add linting (flake8, black, isort)
- Add security scanning
- Add performance benchmarks
- Deploy to staging before production

## License

This is a demo/learning project demonstrating Django testing best practices. Use freely for educational purposes.
