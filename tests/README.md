# Test Suite

Comprehensive unit and integration tests for the Zoom to Drive application.

## Overview

- **Total Tests**: 52
- **Test Coverage**: 73%
- **Framework**: pytest 8.3.4

## Test Structure

### Unit Tests

**test_zoom_client.py** (13 tests)
- OAuth token management and caching
- User lookup by email
- Recordings retrieval
- Duration calculation
- File download with progress tracking
- Timezone conversion (Melbourne)
- File type mapping

**test_rclone_client.py** (14 tests)
- rclone binary availability checks
- Remote configuration validation
- Directory upload operations
- File existence checking
- Drive file ID extraction
- Connection testing
- Error handling

**test_slack_client.py** (8 tests)
- Webhook initialization
- Notification sending
- Message structure validation
- Drive link formatting
- Error handling
- Missing webhook handling

**test_main.py** (17 tests)
- Logging configuration
- File cleanup operations
- CLI argument parsing
- Integration workflow testing
- Error handling
- Short recording filtering

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_zoom_client.py

# Run specific test
pytest tests/test_zoom_client.py::TestZoomClient::test_init

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Coverage Reports

```bash
# Terminal coverage report
pytest --cov=zoom_manager

# HTML coverage report
pytest --cov=zoom_manager --cov-report=html
# Open htmlcov/index.html in browser

# Coverage with missing lines
pytest --cov=zoom_manager --cov-report=term-missing
```

### Debugging Tests

```bash
# Show print statements
pytest -s

# Stop at first failure
pytest -x

# Show local variables in tracebacks
pytest -l

# Enter debugger on failure
pytest --pdb
```

## Test Fixtures

Defined in `conftest.py`:

- `mock_zoom_user`: Sample Zoom user data
- `mock_zoom_recording`: Sample recording with files
- `mock_zoom_recordings_response`: API response format
- `mock_oauth_token_response`: OAuth token response
- `mock_rclone_listremotes`: rclone remote list output
- `mock_rclone_lsjson_response`: File metadata from rclone
- `mock_slack_response`: Slack webhook response
- `temp_download_dir`: Temporary directory for file operations
- `sample_downloaded_file`: Mock downloaded file structure

## Test Markers

- `@pytest.mark.unit`: Unit tests (mock external dependencies)
- `@pytest.mark.integration`: Integration tests (test component interactions)
- `@pytest.mark.slow`: Tests that take longer to run

## Coverage Breakdown

| Component | Coverage |
|-----------|----------|
| settings.py | 97% |
| slack_client.py | 89% |
| main.py | 85% |
| zoom_client.py | 69% |
| rclone_client.py | 61% |

## CI/CD Integration

To add tests to CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=zoom_manager --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Writing New Tests

### Test Template

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
class TestYourComponent:
    """Test suite for YourComponent."""

    def test_your_feature(self):
        """Test description."""
        # Arrange
        component = YourComponent()

        # Act
        result = component.your_method()

        # Assert
        assert result == expected_value
```

### Best Practices

1. **Use descriptive test names** - Test names should explain what is being tested
2. **Follow AAA pattern** - Arrange, Act, Assert
3. **Mock external dependencies** - Use `@patch` for API calls, file operations
4. **Test edge cases** - Include tests for error conditions
5. **Keep tests isolated** - Each test should be independent
6. **Use fixtures** - Share common test data via conftest.py

## Continuous Improvement

Areas for increased coverage:
- `rclone_client.py`: Upload error handling, remote info parsing
- `zoom_client.py`: File processing workflow, error recovery
- `main.py`: Additional workflow scenarios, error cases

## Dependencies

Defined in `requirements-test.txt`:
- pytest==8.3.4
- pytest-cov==6.0.0
- pytest-mock==3.14.0
