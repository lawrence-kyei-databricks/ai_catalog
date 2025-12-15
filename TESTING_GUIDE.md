# CarMax Data Classification Platform - Testing Guide

## Quick Start

### 1. Setup Test Environment

```bash
# Clone/navigate to project
cd /Users/lawrence.kyei/Desktop/dbx-demos/ai_catalog

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### 2. Run Tests

#### Option A: Using Test Runner Script (Recommended)

```bash
# Make script executable (first time only)
chmod +x run_tests.sh

# Run all tests
./run_tests.sh

# Run with coverage report
./run_tests.sh coverage

# Run unit tests only
./run_tests.sh unit

# Run integration tests only
./run_tests.sh integration

# Run in parallel (faster)
./run_tests.sh fast
```

#### Option B: Using pytest directly

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_taxonomy_manager.py

# Run specific test class
pytest tests/unit/test_taxonomy_manager.py::TestExcelImport

# Run specific test
pytest tests/unit/test_taxonomy_manager.py::TestExcelImport::test_import_from_excel_success
```

## Test Organization

### Directory Structure

```
tests/
├── __init__.py                          # Package init
├── conftest.py                          # Shared fixtures (45+ fixtures)
├── data/
│   └── sample_elements.json             # Test data
├── unit/                                # Unit tests (isolated components)
│   ├── test_taxonomy_manager.py         # TaxonomyManager (45 tests)
│   └── test_classification_engine.py    # ClassificationEngine (60 tests)
└── integration/                         # Integration tests (API endpoints)
    └── test_flask_api.py                # Flask API (50 tests)
```

### Test Categories

| Category | Description | Count | Location |
|----------|-------------|-------|----------|
| Unit Tests | Isolated component tests | 105 | `tests/unit/` |
| Integration Tests | API endpoint tests | 50 | `tests/integration/` |
| Total | | 155+ | |

## Test Coverage by Component

### 1. TaxonomyManager (45 Tests)

**File:** `tests/unit/test_taxonomy_manager.py`

#### Test Classes

```
TestTaxonomyManagerInit (2 tests)
├── Workspace client initialization
└── Schema configuration

TestElementIdGeneration (5 tests)
├── Basic conversion
├── Special character removal
├── Space handling
├── Multiple space handling
└── Underscore stripping

TestKeywordExtraction (7 tests)
├── Original name inclusion
├── SSN abbreviations
├── Email abbreviations
├── Phone abbreviations
├── Credit card abbreviations
├── DOB abbreviations
└── Duplicate removal

TestSQLQuoting (5 tests)
├── Normal string quoting
├── Single quote escaping
├── None/NULL handling
├── NaN handling
└── Number conversion

TestExcelImport (6 tests)
├── Successful import
├── MERGE statement creation
├── Error handling
├── Missing file handling
├── Malformed file handling
└── Category counting

TestUCTagSync (2 tests)
├── Tag creation
└── Error handling

TestVersionTracking (2 tests)
├── Version record creation
└── Current version retrieval

TestGetActiveTaxonomy (2 tests)
├── Structure validation
└── Sensitive element counting

TestSQLExecution (4 tests)
├── Successful execution
├── No results handling
├── Failure handling
└── Async completion
```

#### Example Test Execution

```bash
# Run all TaxonomyManager tests
pytest tests/unit/test_taxonomy_manager.py -v

# Run Excel import tests only
pytest tests/unit/test_taxonomy_manager.py::TestExcelImport -v

# Run specific test
pytest tests/unit/test_taxonomy_manager.py::TestExcelImport::test_import_from_excel_success -vv
```

### 2. ClassificationEngine (60 Tests)

**File:** `tests/unit/test_classification_engine.py`

#### Test Classes

```
TestClassificationEngineInit (4 tests)
TestGetColumnInfo (4 tests)
TestPatternDetection (8 tests)
TestFingerprintGeneration (4 tests)
TestCacheLookup (3 tests)
TestClaudeAPIIntegration (5 tests)
TestBuildClassificationPrompt (5 tests)
TestAutoApprovalDecision (7 tests)
TestPatternRules (7 tests)
TestClassifyColumn (3 tests)
TestStoreClassification (2 tests)
```

#### Example Test Execution

```bash
# Run all ClassificationEngine tests
pytest tests/unit/test_classification_engine.py -v

# Run auto-approval tests only
pytest tests/unit/test_classification_engine.py::TestAutoApprovalDecision -v

# Run pattern matching tests
pytest tests/unit/test_classification_engine.py::TestPatternRules -v

# Run with pattern filter
pytest tests/unit/test_classification_engine.py -k "pattern" -v
```

### 3. Flask API (50 Tests)

**File:** `tests/integration/test_flask_api.py`

#### Test Classes

```
TestTaxonomyEndpoints (4 tests)
├── Import taxonomy
├── Get taxonomy
└── Error handling

TestCatalogSchemaEndpoints (4 tests)
├── List catalogs
├── List schemas
└── Default handling

TestClassificationEndpoints (6 tests)
├── Classify columns
├── Get classifications
├── Filtering
└── Limits

TestApprovalEndpoints (6 tests)
├── Approve
├── Reject
└── Bulk approve

TestTagApplicationEndpoint (4 tests)
├── Apply tags
├── Error collection
└── ALTER TABLE validation

TestDashboardEndpoint (2 tests)
TestStaticFileServing (2 tests)
TestHelperFunctions (2 tests)
TestErrorHandling (3 tests)
TestRequestValidation (3 tests)
TestCORS (1 test)
```

#### Example Test Execution

```bash
# Run all Flask API tests
pytest tests/integration/test_flask_api.py -v

# Run approval workflow tests
pytest tests/integration/test_flask_api.py::TestApprovalEndpoints -v

# Run classification endpoint tests
pytest tests/integration/test_flask_api.py::TestClassificationEndpoints -v
```

## Running Tests by Scenario

### Test Excel Import Workflow

```bash
# Test complete import workflow
pytest tests/unit/test_taxonomy_manager.py::TestExcelImport -v

# Test specific scenarios
pytest tests/unit/test_taxonomy_manager.py::TestExcelImport::test_import_from_excel_success -v
pytest tests/unit/test_taxonomy_manager.py::TestExcelImport::test_import_from_excel_malformed_file -v
```

### Test Classification Workflow

```bash
# Test complete classification workflow
pytest tests/unit/test_classification_engine.py::TestClassifyColumn -v

# Test pattern matching
pytest tests/unit/test_classification_engine.py::TestPatternRules -v

# Test auto-approval
pytest tests/unit/test_classification_engine.py::TestAutoApprovalDecision -v
```

### Test API Endpoints

```bash
# Test all API endpoints
pytest tests/integration/test_flask_api.py -v

# Test specific endpoint
pytest tests/integration/test_flask_api.py::TestClassificationEndpoints::test_classify_columns_success -v
```

### Test Error Handling

```bash
# Find all error handling tests
pytest -k "error" -v

# Test specific error scenarios
pytest tests/unit/test_taxonomy_manager.py -k "error" -v
pytest tests/unit/test_classification_engine.py -k "error" -v
pytest tests/integration/test_flask_api.py::TestErrorHandling -v
```

## Coverage Reports

### Generate Coverage Report

```bash
# Generate HTML report
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Generate Multiple Report Formats

```bash
# HTML + Terminal + XML (for CI/CD)
pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml
```

### Coverage by Component

```bash
# TaxonomyManager coverage only
pytest tests/unit/test_taxonomy_manager.py --cov=app.taxonomy_manager --cov-report=term-missing

# ClassificationEngine coverage only
pytest tests/unit/test_classification_engine.py --cov=app.classification_engine --cov-report=term-missing

# Flask API coverage only
pytest tests/integration/test_flask_api.py --cov=app.main --cov-report=term-missing
```

## Advanced Test Execution

### Parallel Execution (Faster)

```bash
# Run tests in parallel using all CPU cores
pytest -n auto

# Run tests using specific number of workers
pytest -n 4
```

### Stop on First Failure

```bash
pytest -x
```

### Show Local Variables on Failure

```bash
pytest -l
```

### Run Last Failed Tests Only

```bash
pytest --lf
```

### Run Failed Tests First, Then Others

```bash
pytest --ff
```

### Increase Verbosity

```bash
# Standard verbose
pytest -v

# Extra verbose (shows individual assertions)
pytest -vv

# Show print statements
pytest -s
```

## Debugging Tests

### Interactive Debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on errors
pytest --pdbcls=IPython.terminal.debugger:TerminalPdb
```

### Show Warnings

```bash
pytest -W all
```

### Trace Execution

```bash
pytest --trace
```

## Test Markers

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

### List Available Markers

```bash
pytest --markers
```

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/tests.yml`:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml --cov-report=term-missing

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
# Add app directory to Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}/app"

# Or run from project root
cd /Users/lawrence.kyei/Desktop/dbx-demos/ai_catalog
pytest
```

#### 2. Fixture Not Found

**Problem:** `fixture 'mock_workspace_client' not found`

**Solution:**
- Ensure `conftest.py` is in tests directory
- Check fixture name spelling
- Verify pytest can find conftest.py

#### 3. Mock Not Working

**Problem:** Real API calls being made instead of mocks

**Solution:**
```python
# Use patch decorator correctly
@patch('main.w', new_callable=lambda: mock_workspace_client)
def test_example(self, mock_w):
    # Test code
```

#### 4. Coverage Not Working

**Problem:** Coverage report shows 0%

**Solution:**
```bash
# Install coverage
pip install pytest-cov

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

## Test Development Workflow

### Adding New Tests

1. **Identify component to test**
   ```bash
   # Determine if unit or integration test
   # Unit: tests/unit/
   # Integration: tests/integration/
   ```

2. **Create test file** (if needed)
   ```bash
   touch tests/unit/test_new_component.py
   ```

3. **Write test**
   ```python
   import pytest
   from new_component import NewComponent

   class TestNewComponent:
       def test_basic_functionality(self, mock_workspace_client):
           # Arrange
           component = NewComponent(mock_workspace_client)

           # Act
           result = component.do_something()

           # Assert
           assert result == expected_value
   ```

4. **Run test**
   ```bash
   pytest tests/unit/test_new_component.py -v
   ```

5. **Check coverage**
   ```bash
   pytest tests/unit/test_new_component.py --cov=app.new_component --cov-report=term-missing
   ```

6. **Commit**
   ```bash
   git add tests/unit/test_new_component.py
   git commit -m "Add tests for NewComponent"
   ```

## Performance Benchmarking

### Measure Test Execution Time

```bash
# Show duration of slowest tests
pytest --durations=10

# Show duration of all tests
pytest --durations=0
```

### Profile Tests

```bash
# Install pytest-profiling
pip install pytest-profiling

# Run with profiling
pytest --profile
```

## Best Practices

### 1. Test Independence
- Each test should run independently
- No shared state between tests
- Use fresh fixtures for each test

### 2. Clear Test Names
```python
# Good
def test_import_from_excel_success(self, ...):

# Bad
def test_import(self, ...):
```

### 3. Arrange-Act-Assert
```python
def test_example(self):
    # Arrange: Set up test data
    data = create_test_data()

    # Act: Perform action
    result = process_data(data)

    # Assert: Verify outcome
    assert result == expected
```

### 4. One Assertion Per Test (when possible)
```python
# Good
def test_element_id_lowercase(self):
    assert generate_id("Test") == "test"

def test_element_id_underscores(self):
    assert generate_id("Test Name") == "test_name"

# Acceptable for related assertions
def test_import_result_structure(self):
    result = import_taxonomy(...)
    assert 'elements_imported' in result
    assert 'version' in result
    assert result['elements_imported'] > 0
```

## Summary

### Quick Reference

| Task | Command |
|------|---------|
| Run all tests | `./run_tests.sh` or `pytest` |
| Run with coverage | `./run_tests.sh coverage` |
| Run unit tests | `./run_tests.sh unit` |
| Run integration tests | `./run_tests.sh integration` |
| Run specific file | `pytest tests/unit/test_taxonomy_manager.py` |
| Run specific test | `pytest tests/unit/test_taxonomy_manager.py::test_name` |
| Run in parallel | `pytest -n auto` |
| Generate coverage report | `pytest --cov=app --cov-report=html` |
| Debug on failure | `pytest --pdb` |
| Verbose output | `pytest -vv` |

### Test Statistics

- **Total Tests:** 155+
- **Test Files:** 3
- **Fixtures:** 45+
- **Coverage Target:** 88%+
- **Execution Time:** ~30 seconds (sequential), ~10 seconds (parallel)

### Next Steps

1. Run the test suite: `./run_tests.sh coverage`
2. Review the coverage report: `open htmlcov/index.html`
3. Identify any gaps in coverage
4. Add tests for uncovered code paths
5. Integrate into CI/CD pipeline
