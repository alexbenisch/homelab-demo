# Testing Guide: Django unittest vs pytest

This document explains how to run tests and highlights the key differences between Django's built-in unittest framework and pytest.

## Quick Start

### Install Test Dependencies

```bash
# Install pytest and related packages
pip install -e ".[test]"
```

### Running Django unittest Tests

```bash
# Run all tests using Django's test runner
cd src
python manage.py test

# Run tests for a specific app
python manage.py test core

# Run a specific test class
python manage.py test core.tests.HomeViewTestCase

# Run a specific test method
python manage.py test core.tests.HomeViewTestCase.test_home_view_status_code

# Run with verbosity
python manage.py test --verbosity=2
```

### Running pytest Tests

```bash
# Run all tests (from project root)
pytest

# Run only pytest tests (exclude Django's tests.py)
pytest src/core/test_pytest.py

# Run a specific test class
pytest src/core/test_pytest.py::TestHomeView

# Run a specific test method
pytest src/core/test_pytest.py::TestHomeView::test_home_view_status_code

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=core --cov-report=term-missing

# Run and reuse database (faster for repeated runs)
pytest --reuse-db

# Run with specific markers
pytest -m "not slow"
```

## Key Differences: unittest vs pytest

### 1. Test Structure

**Django unittest (tests.py)**
```python
from django.test import TestCase

class HomeViewTestCase(TestCase):
    def setUp(self):
        """Runs before each test method"""
        self.client = Client()

    def test_home_view(self):
        """Test using self.assert* methods"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
```

**pytest (test_pytest.py)**
```python
import pytest

@pytest.mark.django_db
class TestHomeView:
    def test_home_view(self, client):
        """Test using simple assert statements"""
        response = client.get('/')
        assert response.status_code == 200
```

### 2. Assertions

**Django unittest**
- Uses `self.assertEqual()`, `self.assertTrue()`, `self.assertIn()`, etc.
- Specialized assertions like `self.assertTemplateUsed()`
- More verbose but explicit

**pytest**
- Uses simple `assert` statements
- More Pythonic and concise
- Better error messages showing actual vs expected values

### 3. Fixtures vs setUp/tearDown

**Django unittest**
```python
class MyTestCase(TestCase):
    def setUp(self):
        """Runs before EACH test"""
        self.user = User.objects.create(username='test')

    def tearDown(self):
        """Runs after EACH test"""
        pass

    @classmethod
    def setUpTestData(cls):
        """Runs ONCE for the entire class"""
        cls.shared_data = "shared"
```

**pytest**
```python
@pytest.fixture
def user(db):
    """Reusable fixture - can control scope"""
    return User.objects.create(username='test')

@pytest.fixture(scope='class')
def shared_data():
    """Class-scoped fixture"""
    return "shared"

def test_something(user, shared_data):
    """Fixtures injected as function arguments"""
    assert user.username == 'test'
```

### 4. Test Discovery

**Django unittest**
- Looks for files named `tests.py` or `tests/` directories
- Must use TestCase classes
- Run with `python manage.py test`

**pytest**
- Looks for `test_*.py` or `*_test.py` files
- Can use classes (Test*) or standalone functions
- Run with `pytest` command
- More flexible naming conventions

### 5. Parametrization

**Django unittest**
```python
# No built-in parametrization
# Need to write separate test methods or use loops
def test_multiple_urls(self):
    urls = ['/', '/health/', '/info/']
    for url in urls:
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
```

**pytest**
```python
@pytest.mark.parametrize("url,expected", [
    ('/', 200),
    ('/health/', 200),
    ('/info/', 200),
])
def test_url_status(client, url, expected):
    """Runs as 3 separate tests"""
    response = client.get(url)
    assert response.status_code == expected
```

### 6. Test Database

**Django unittest**
- Automatically creates and destroys test database
- Each test runs in a transaction (rolled back after test)
- Use `TestCase` for transaction-based tests
- Use `TransactionTestCase` if you need to test transaction behavior

**pytest**
- Requires `@pytest.mark.django_db` decorator
- Can use `--reuse-db` flag for faster repeated runs
- Can use `@pytest.fixture(scope='module')` for database fixtures
- More control over database creation/destruction

### 7. Plugin Ecosystem

**Django unittest**
- Built into Django
- Limited to Django's testing features
- No additional dependencies needed

**pytest**
- Rich plugin ecosystem
- pytest-django for Django integration
- pytest-cov for coverage
- pytest-xdist for parallel testing
- Many more plugins available

## Advanced Features

### Pytest Markers

```python
@pytest.mark.slow
def test_slow_operation(client):
    """Mark slow tests"""
    pass

# Run all tests except slow ones
# pytest -m "not slow"
```

### Pytest Fixtures with Different Scopes

```python
@pytest.fixture(scope='session')
def expensive_setup():
    """Runs once for entire test session"""
    return setup_expensive_resource()

@pytest.fixture(scope='module')
def shared_user(db):
    """Runs once per test module"""
    return User.objects.create(username='shared')

@pytest.fixture(scope='function')  # Default
def unique_user(db):
    """Runs for each test function"""
    return User.objects.create(username='unique')
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=core --cov-report=html

# Open htmlcov/index.html in browser to see coverage
```

## Which Should You Use?

### Use Django unittest when:
- You're already familiar with unittest
- You want Django-specific assertions (assertTemplateUsed, etc.)
- You're working on a team that uses unittest
- You don't want additional dependencies

### Use pytest when:
- You want more concise test code
- You need advanced features (parametrization, fixtures, markers)
- You want better test output and debugging
- You're starting a new project
- You want to leverage pytest's plugin ecosystem

### Use Both?
- Yes! You can run both in the same project
- Django's test runner can run unittest tests
- pytest can run both unittest and pytest tests
- Keep them in separate files for clarity

## Test File Locations

```
demo-django/
├── src/
│   └── core/
│       ├── tests.py          # Django unittest tests
│       └── test_pytest.py    # pytest tests
├── pytest.ini                # pytest configuration
└── pyproject.toml           # Dependencies and pytest config
```

## Common Commands Reference

```bash
# Django unittest
python manage.py test                    # Run all tests
python manage.py test core               # Run app tests
python manage.py test --parallel         # Run in parallel
python manage.py test --keepdb          # Keep test database

# pytest
pytest                                   # Run all tests
pytest -v                               # Verbose output
pytest -x                               # Stop on first failure
pytest --lf                             # Run last failed tests
pytest --reuse-db                       # Reuse test database
pytest -k "health"                      # Run tests matching pattern
pytest --collect-only                   # Show what tests will run
```

## Tips and Best Practices

1. **Choose one style per file** - Don't mix unittest and pytest in the same file
2. **Use descriptive test names** - Test names should describe what they test
3. **Keep tests independent** - Tests should not depend on each other
4. **Use fixtures/setUp for common data** - Don't repeat setup code
5. **Test one thing per test** - Makes failures easier to debug
6. **Use parametrization** - Avoid duplicate test code
7. **Mock external services** - Tests should be fast and reliable
8. **Run tests frequently** - Integrate with CI/CD pipeline
