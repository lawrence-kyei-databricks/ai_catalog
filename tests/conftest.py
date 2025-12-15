"""
Pytest configuration and shared fixtures for CarMax Data Classification Platform tests
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock
from datetime import datetime
import pandas as pd
import json

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


# ========================================
# MOCK DATABRICKS SDK
# ========================================

@pytest.fixture
def mock_workspace_client():
    """Mock Databricks WorkspaceClient"""
    mock_client = Mock()

    # Mock statement execution
    mock_statement = Mock()
    mock_statement.statement_id = "test-statement-123"
    mock_statement.status.state = "SUCCEEDED"
    mock_statement.status.error = None
    mock_statement.result = Mock()
    mock_statement.manifest = Mock()

    mock_client.statement_execution.execute_statement.return_value = mock_statement
    mock_client.statement_execution.get_statement.return_value = mock_statement

    # Mock catalogs
    mock_catalog = Mock()
    mock_catalog.name = "main"
    mock_client.catalogs.list.return_value = [mock_catalog]

    # Mock schemas
    mock_schema = Mock()
    mock_schema.name = "carmax_taxonomy"
    mock_client.schemas.list.return_value = [mock_schema]

    return mock_client


@pytest.fixture
def mock_sql_results():
    """Factory for creating mock SQL results"""
    def _create_results(data_rows, column_names=None):
        """
        Create mock SQL result structure

        Args:
            data_rows: List of dicts or list of lists
            column_names: List of column names (required if data_rows are lists)
        """
        if not data_rows:
            return []

        # If data_rows are dicts, extract column names
        if isinstance(data_rows[0], dict):
            return data_rows

        # If data_rows are lists, zip with column_names
        if column_names:
            return [dict(zip(column_names, row)) for row in data_rows]

        raise ValueError("column_names required when data_rows are lists")

    return _create_results


# ========================================
# SAMPLE DATA FIXTURES
# ========================================

@pytest.fixture
def sample_elements_df():
    """Sample taxonomy elements DataFrame"""
    data = {
        'Data Element Name': [
            'Social Security Number',
            'Email Address',
            'Phone Number',
            'Credit Card / Debit Card Number',
            'First Name'
        ],
        'Data Category': [
            'Identifiers',
            'Identifiers',
            'Identifiers',
            'Payment Card Info',
            'Demographic Info'
        ],
        'Description': [
            'Government issued identification number',
            'Electronic mail address',
            'Telephone contact number',
            'Payment card number',
            'Individual given name'
        ],
        'Sensitive_Flag': ['Yes', 'No', 'No', 'Yes', 'No'],
        'Data Classification': ['PII', 'PII', 'PII', 'PCI', 'PII']
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_subjects_df():
    """Sample subject types DataFrame"""
    data = {
        'Data Subject Type Id': ['associate', 'b2b', 'consumer'],
        'Data Subject Type Name': ['Associate', 'B2B', 'Consumer'],
        'Description': [
            'Internal personnel (employees, contractors)',
            'External business contacts (vendors, partners)',
            'Individual customers'
        ]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_column_info():
    """Sample column information for classification"""
    return {
        'catalog': 'main',
        'schema': 'test_schema',
        'table': 'customers',
        'column_name': 'email',
        'column_type': 'string',
        'sample_values': [
            'john.doe@example.com',
            'jane.smith@test.com',
            'bob.jones@demo.org'
        ],
        'full_name': 'main.test_schema.customers.email'
    }


@pytest.fixture
def sample_taxonomy():
    """Sample taxonomy structure"""
    return {
        'elements': [
            {
                'element_id': 'social_security_number',
                'element_name': 'Social Security Number',
                'element_category': 'Identifiers',
                'element_description': 'Government issued identification number',
                'sensitive_flag': 'Yes',
                'keywords': ['ssn', 'social_sec', 'social_security']
            },
            {
                'element_id': 'email_address',
                'element_name': 'Email Address',
                'element_category': 'Identifiers',
                'element_description': 'Electronic mail address',
                'sensitive_flag': 'No',
                'keywords': ['email', 'e_mail', 'email_addr']
            },
            {
                'element_id': 'phone_number',
                'element_name': 'Phone Number',
                'element_category': 'Identifiers',
                'element_description': 'Telephone contact number',
                'sensitive_flag': 'No',
                'keywords': ['phone', 'telephone', 'mobile', 'cell']
            }
        ],
        'subjects': ['Associate', 'B2B', 'Consumer'],
        'categories': [
            {'category_name': 'Identifiers', 'element_count': 3}
        ],
        'total_elements': 3,
        'total_sensitive': 1,
        'version': '1.0'
    }


@pytest.fixture
def sample_claude_response():
    """Sample Claude API classification response"""
    return {
        'element': 'Email Address',
        'category': 'Identifiers',
        'confidence': 95.5,
        'sensitive': False,
        'subjects': ['Associate', 'Consumer'],
        'reasoning': 'Column name "email" and sample values matching email pattern clearly indicate Email Address'
    }


# ========================================
# EXCEL TEST FILES
# ========================================

@pytest.fixture
def create_test_excel_files(tmp_path):
    """Factory to create test Excel files"""
    def _create_files(elements_data=None, subjects_data=None):
        if elements_data is None:
            elements_data = {
                'Data Element Name': ['Test Element'],
                'Data Category': ['Test Category'],
                'Description': ['Test description'],
                'Sensitive_Flag': ['No'],
                'Data Classification': ['Public']
            }

        if subjects_data is None:
            subjects_data = {
                'Data Subject Type Id': ['test_subject'],
                'Data Subject Type Name': ['Test Subject'],
                'Description': ['Test subject description']
            }

        elements_file = tmp_path / "elements.xlsx"
        subjects_file = tmp_path / "subjects.xlsx"

        pd.DataFrame(elements_data).to_excel(elements_file, index=False)
        pd.DataFrame(subjects_data).to_excel(subjects_file, index=False)

        return str(elements_file), str(subjects_file)

    return _create_files


@pytest.fixture
def malformed_excel_file(tmp_path):
    """Create malformed Excel file for error testing"""
    file_path = tmp_path / "malformed.xlsx"

    # Missing required columns
    data = {
        'Wrong Column': ['data1', 'data2'],
        'Another Wrong': ['data3', 'data4']
    }

    pd.DataFrame(data).to_excel(file_path, index=False)
    return str(file_path)


# ========================================
# FLASK APP FIXTURES
# ========================================

@pytest.fixture
def flask_app(mock_workspace_client, monkeypatch):
    """Create Flask test app with mocked dependencies"""
    # Mock the WorkspaceClient import
    monkeypatch.setattr('main.w', mock_workspace_client)
    monkeypatch.setattr('main.WAREHOUSE_ID', 'test-warehouse-123')

    from main import app
    app.config['TESTING'] = True
    return app


@pytest.fixture
def flask_client(flask_app):
    """Flask test client"""
    return flask_app.test_client()


# ========================================
# PATTERN MATCHING FIXTURES
# ========================================

@pytest.fixture
def sample_ssn_data():
    """Sample SSN data for pattern matching"""
    return {
        'column_name': 'customer_ssn',
        'sample_values': [
            '123-45-6789',
            '987-65-4321',
            '555-12-3456'
        ]
    }


@pytest.fixture
def sample_email_data():
    """Sample email data for pattern matching"""
    return {
        'column_name': 'email_address',
        'sample_values': [
            'test@example.com',
            'user@domain.org',
            'admin@company.net'
        ]
    }


@pytest.fixture
def sample_phone_data():
    """Sample phone data for pattern matching"""
    return {
        'column_name': 'phone',
        'sample_values': [
            '555-123-4567',
            '555-987-6543',
            '555-555-5555'
        ]
    }


@pytest.fixture
def sample_credit_card_data():
    """Sample credit card data for pattern matching"""
    return {
        'column_name': 'cc_number',
        'sample_values': [
            '4532-1234-5678-9010',
            '5425-2334-3010-9903',
            '3782-822463-10005'
        ]
    }


# ========================================
# CLASSIFICATION RESULT FIXTURES
# ========================================

@pytest.fixture
def tier1_classification():
    """Tier 1 auto-approval classification (highest confidence)"""
    return {
        'element': 'Social Security Number',
        'category': 'Identifiers',
        'confidence': 99.0,
        'sensitive': True,
        'pattern_match_score': 0.95,
        'subjects': ['Associate', 'Consumer'],
        'reasoning': 'Pattern match: 100% samples match SSN pattern'
    }


@pytest.fixture
def tier2_classification():
    """Tier 2 auto-approval classification (good confidence, non-sensitive)"""
    return {
        'element': 'Email Address',
        'category': 'Identifiers',
        'confidence': 88.0,
        'sensitive': False,
        'subjects': ['Associate', 'Consumer'],
        'reasoning': 'Email pattern match with high confidence'
    }


@pytest.fixture
def tier3_classification():
    """Tier 3 classification (requires human review)"""
    return {
        'element': 'Custom Field',
        'category': 'Custom Category',
        'confidence': 65.0,
        'sensitive': True,
        'subjects': ['Consumer'],
        'reasoning': 'Low confidence on sensitive data'
    }


# ========================================
# DATABASE MOCK HELPERS
# ========================================

@pytest.fixture
def mock_execute_sql(monkeypatch):
    """Factory for mocking _execute_sql method"""
    def _mock_sql(return_value):
        """
        Mock _execute_sql to return specific value

        Args:
            return_value: Value to return from SQL execution
        """
        mock_func = Mock(return_value=return_value)
        return mock_func

    return _mock_sql


@pytest.fixture
def capture_sql_calls():
    """Fixture to capture SQL calls for verification"""
    calls = []

    def capture(sql):
        calls.append(sql)
        return []

    capture.calls = calls
    return capture
