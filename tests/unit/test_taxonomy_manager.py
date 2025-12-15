"""
Unit tests for TaxonomyManager
Tests Excel import, CRUD operations, UC tag creation, and version tracking
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, call
from taxonomy_manager import TaxonomyManager


class TestTaxonomyManagerInit:
    """Test TaxonomyManager initialization"""

    def test_init_sets_workspace_client(self, mock_workspace_client):
        """Should initialize with WorkspaceClient"""
        tm = TaxonomyManager(mock_workspace_client)
        assert tm.w == mock_workspace_client

    def test_init_sets_default_schemas(self, mock_workspace_client):
        """Should set default schema names"""
        tm = TaxonomyManager(mock_workspace_client)
        assert tm.taxonomy_schema == "main.carmax_taxonomy"
        assert tm.tags_schema == "main.carmax_tags"


class TestElementIdGeneration:
    """Test element ID generation"""

    def test_generate_element_id_basic(self, mock_workspace_client):
        """Should convert element name to lowercase underscore format"""
        tm = TaxonomyManager(mock_workspace_client)

        assert tm._generate_element_id("Social Security Number") == "social_security_number"
        assert tm._generate_element_id("Email Address") == "email_address"
        assert tm._generate_element_id("Phone Number") == "phone_number"

    def test_generate_element_id_removes_special_chars(self, mock_workspace_client):
        """Should remove special characters"""
        tm = TaxonomyManager(mock_workspace_client)

        assert tm._generate_element_id("Credit Card / Debit Card") == "credit_card_debit_card"
        assert tm._generate_element_id("Name (First)") == "name_first"
        assert tm._generate_element_id("Tax-ID#") == "taxid"

    def test_generate_element_id_handles_multiple_spaces(self, mock_workspace_client):
        """Should handle multiple spaces correctly"""
        tm = TaxonomyManager(mock_workspace_client)

        assert tm._generate_element_id("Test   Multiple    Spaces") == "test_multiple_spaces"

    def test_generate_element_id_strips_underscores(self, mock_workspace_client):
        """Should strip leading/trailing underscores"""
        tm = TaxonomyManager(mock_workspace_client)

        assert tm._generate_element_id("_Leading") == "leading"
        assert tm._generate_element_id("Trailing_") == "trailing"


class TestKeywordExtraction:
    """Test keyword extraction from element names"""

    def test_extract_keywords_includes_original(self, mock_workspace_client):
        """Should include original element name in lowercase"""
        tm = TaxonomyManager(mock_workspace_client)

        keywords = tm._extract_keywords("Test Element")
        assert "test element" in keywords

    def test_extract_keywords_ssn_abbreviations(self, mock_workspace_client):
        """Should extract SSN abbreviations"""
        tm = TaxonomyManager(mock_workspace_client)

        keywords = tm._extract_keywords("Social Security Number")
        assert "ssn" in keywords
        assert "social_sec" in keywords
        assert "social_security" in keywords

    def test_extract_keywords_email_abbreviations(self, mock_workspace_client):
        """Should extract email abbreviations"""
        tm = TaxonomyManager(mock_workspace_client)

        keywords = tm._extract_keywords("Email Address")
        assert "email" in keywords
        assert "e_mail" in keywords
        assert "email_addr" in keywords

    def test_extract_keywords_phone_abbreviations(self, mock_workspace_client):
        """Should extract phone abbreviations"""
        tm = TaxonomyManager(mock_workspace_client)

        keywords = tm._extract_keywords("Phone Number")
        assert "phone" in keywords
        assert "telephone" in keywords
        assert "mobile" in keywords
        assert "cell" in keywords

    def test_extract_keywords_credit_card_abbreviations(self, mock_workspace_client):
        """Should extract credit card abbreviations"""
        tm = TaxonomyManager(mock_workspace_client)

        keywords = tm._extract_keywords("Credit Card Number")
        assert "cc" in keywords
        assert "credit_card" in keywords
        assert "card_number" in keywords

    def test_extract_keywords_dob_abbreviations(self, mock_workspace_client):
        """Should extract date of birth abbreviations"""
        tm = TaxonomyManager(mock_workspace_client)

        keywords = tm._extract_keywords("Date of Birth")
        assert "dob" in keywords
        assert "birth_date" in keywords
        assert "birthdate" in keywords

    def test_extract_keywords_removes_duplicates(self, mock_workspace_client):
        """Should remove duplicate keywords"""
        tm = TaxonomyManager(mock_workspace_client)

        keywords = tm._extract_keywords("Email")
        # Should not have duplicates
        assert len(keywords) == len(set(keywords))


class TestSQLQuoting:
    """Test SQL string quoting helper"""

    def test_quote_normal_string(self, mock_workspace_client):
        """Should wrap string in single quotes"""
        tm = TaxonomyManager(mock_workspace_client)

        assert tm._quote("test") == "'test'"
        assert tm._quote("Test Value") == "'Test Value'"

    def test_quote_escapes_single_quotes(self, mock_workspace_client):
        """Should escape single quotes by doubling them"""
        tm = TaxonomyManager(mock_workspace_client)

        assert tm._quote("It's a test") == "'It''s a test'"
        assert tm._quote("O'Brien") == "'O''Brien'"

    def test_quote_handles_none(self, mock_workspace_client):
        """Should return NULL for None values"""
        tm = TaxonomyManager(mock_workspace_client)

        assert tm._quote(None) == "NULL"

    def test_quote_handles_nan(self, mock_workspace_client):
        """Should return NULL for pandas NaN values"""
        tm = TaxonomyManager(mock_workspace_client)

        assert tm._quote(float('nan')) == "NULL"

    def test_quote_converts_numbers_to_string(self, mock_workspace_client):
        """Should convert numbers to quoted strings"""
        tm = TaxonomyManager(mock_workspace_client)

        assert tm._quote(123) == "'123'"
        assert tm._quote(45.67) == "'45.67'"


class TestExcelImport:
    """Test Excel import functionality"""

    @patch.object(TaxonomyManager, '_execute_sql')
    @patch.object(TaxonomyManager, '_sync_uc_tags')
    def test_import_from_excel_success(
        self,
        mock_sync_tags,
        mock_execute_sql,
        mock_workspace_client,
        sample_elements_df,
        sample_subjects_df,
        create_test_excel_files,
        tmp_path
    ):
        """Should successfully import taxonomy from Excel files"""
        # Setup
        elements_file, subjects_file = create_test_excel_files()
        mock_execute_sql.return_value = []
        mock_sync_tags.return_value = 5

        tm = TaxonomyManager(mock_workspace_client)

        # Execute
        result = tm.import_from_excel(elements_file, subjects_file, version="1.0")

        # Verify
        assert result['elements_imported'] == 1  # One element in test file
        assert result['subjects_imported'] == 1
        assert result['tags_created'] == 5
        assert result['version'] == "1.0"
        assert 'timestamp' in result

        # Verify SQL execution was called
        assert mock_execute_sql.called

    @patch.object(TaxonomyManager, '_execute_sql')
    def test_import_elements_creates_merge_statements(
        self,
        mock_execute_sql,
        mock_workspace_client,
        sample_elements_df
    ):
        """Should create MERGE statements for each element"""
        mock_execute_sql.return_value = []
        tm = TaxonomyManager(mock_workspace_client)

        count = tm._import_elements(sample_elements_df)

        # Should call SQL for each element
        assert count == 5
        assert mock_execute_sql.call_count == 5

        # Verify MERGE statement structure
        first_call_sql = mock_execute_sql.call_args_list[0][0][0]
        assert "MERGE INTO" in first_call_sql
        assert "data_elements" in first_call_sql
        assert "WHEN MATCHED THEN" in first_call_sql
        assert "WHEN NOT MATCHED THEN" in first_call_sql

    @patch.object(TaxonomyManager, '_execute_sql')
    def test_import_elements_handles_errors(
        self,
        mock_execute_sql,
        mock_workspace_client,
        sample_elements_df
    ):
        """Should handle errors gracefully and continue processing"""
        # First call succeeds, second fails, third succeeds
        mock_execute_sql.side_effect = [
            [],  # Success
            Exception("DB Error"),  # Failure
            [],  # Success
            [],  # Success
            []   # Success
        ]

        tm = TaxonomyManager(mock_workspace_client)
        count = tm._import_elements(sample_elements_df)

        # Should have imported 4 out of 5 (1 failed)
        assert count == 4

    @patch.object(TaxonomyManager, '_execute_sql')
    def test_import_subjects_creates_merge_statements(
        self,
        mock_execute_sql,
        mock_workspace_client,
        sample_subjects_df
    ):
        """Should create MERGE statements for subject types"""
        mock_execute_sql.return_value = []
        tm = TaxonomyManager(mock_workspace_client)

        tm._import_subjects(sample_subjects_df)

        # Should call SQL for each subject
        assert mock_execute_sql.call_count == 3

        # Verify MERGE statement structure
        first_call_sql = mock_execute_sql.call_args_list[0][0][0]
        assert "MERGE INTO" in first_call_sql
        assert "subject_types" in first_call_sql

    @patch.object(TaxonomyManager, '_execute_sql')
    def test_update_categories_counts_elements(
        self,
        mock_execute_sql,
        mock_workspace_client,
        sample_elements_df
    ):
        """Should count elements per category"""
        mock_execute_sql.return_value = []
        tm = TaxonomyManager(mock_workspace_client)

        tm._update_categories(sample_elements_df)

        # Should create category records
        # Identifiers: 3, Payment Card Info: 1, Demographic Info: 1
        assert mock_execute_sql.call_count == 3

    def test_import_from_excel_missing_file(self, mock_workspace_client, tmp_path):
        """Should raise error if Excel file doesn't exist"""
        tm = TaxonomyManager(mock_workspace_client)

        with pytest.raises(Exception):
            tm.import_from_excel(
                str(tmp_path / "nonexistent.xlsx"),
                str(tmp_path / "nonexistent2.xlsx")
            )

    @patch('pandas.read_excel')
    def test_import_from_excel_malformed_file(
        self,
        mock_read_excel,
        mock_workspace_client
    ):
        """Should handle malformed Excel files"""
        # Simulate missing required columns
        mock_read_excel.return_value = pd.DataFrame({'Wrong Column': ['data']})

        tm = TaxonomyManager(mock_workspace_client)

        with pytest.raises(KeyError):
            tm.import_from_excel("elements.xlsx", "subjects.xlsx")


class TestUCTagSync:
    """Test Unity Catalog tag synchronization"""

    @patch.object(TaxonomyManager, '_execute_sql')
    def test_sync_uc_tags_creates_tags(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should create UC tags for all active elements"""
        # Mock getting elements
        mock_elements = [
            {
                'element_id': 'ssn',
                'element_name': 'Social Security Number',
                'element_description': 'SSN description'
            },
            {
                'element_id': 'email',
                'element_name': 'Email Address',
                'element_description': 'Email description'
            }
        ]

        mock_execute_sql.return_value = mock_elements

        tm = TaxonomyManager(mock_workspace_client)
        tags_created = tm._sync_uc_tags()

        # Should query elements once
        # Then create tag + comment for each element (2 calls per tag)
        # First call gets elements, then 2 elements * 2 calls each = 5 total
        assert mock_execute_sql.call_count == 5
        assert tags_created == 2

    @patch.object(TaxonomyManager, '_execute_sql')
    def test_sync_uc_tags_handles_errors(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should handle tag creation errors gracefully"""
        mock_elements = [
            {'element_id': 'ssn', 'element_name': 'SSN', 'element_description': 'desc'},
            {'element_id': 'email', 'element_name': 'Email', 'element_description': 'desc'}
        ]

        # First call returns elements, subsequent calls fail for first tag, succeed for second
        mock_execute_sql.side_effect = [
            mock_elements,  # Get elements
            Exception("Tag creation failed"),  # First tag CREATE fails
            [],  # Second tag CREATE succeeds
            []   # Second tag COMMENT succeeds
        ]

        tm = TaxonomyManager(mock_workspace_client)
        tags_created = tm._sync_uc_tags()

        # Only second tag should succeed
        assert tags_created == 1


class TestVersionTracking:
    """Test taxonomy version tracking"""

    @patch.object(TaxonomyManager, '_execute_sql')
    def test_create_version_record(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should insert version record"""
        mock_execute_sql.return_value = []
        tm = TaxonomyManager(mock_workspace_client)

        tm._create_version_record("1.0", 172, "INITIAL", "Test import")

        # Verify SQL was called
        assert mock_execute_sql.called
        sql_call = mock_execute_sql.call_args[0][0]
        assert "INSERT INTO" in sql_call
        assert "taxonomy_versions" in sql_call
        assert "1.0" in sql_call
        assert "INITIAL" in sql_call

    @patch.object(TaxonomyManager, '_execute_sql')
    def test_get_current_version(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should retrieve latest version number"""
        mock_execute_sql.return_value = [{'version_number': '2.0'}]
        tm = TaxonomyManager(mock_workspace_client)

        version = tm._get_current_version()

        assert version == '2.0'

    @patch.object(TaxonomyManager, '_execute_sql')
    def test_get_current_version_default(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should return 1.0 if no versions exist"""
        mock_execute_sql.return_value = []
        tm = TaxonomyManager(mock_workspace_client)

        version = tm._get_current_version()

        assert version == '1.0'


class TestGetActiveTaxonomy:
    """Test retrieving active taxonomy"""

    @patch.object(TaxonomyManager, '_execute_sql')
    @patch.object(TaxonomyManager, '_get_current_version')
    def test_get_active_taxonomy_structure(
        self,
        mock_version,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should return complete taxonomy structure"""
        mock_elements = [
            {
                'element_id': 'ssn',
                'element_name': 'SSN',
                'element_category': 'Identifiers',
                'element_description': 'desc',
                'sensitive_flag': 'Yes',
                'keywords': ['ssn']
            }
        ]
        mock_subjects = [{'subject_type_name': 'Consumer', 'subject_description': 'desc'}]
        mock_categories = [{'category_name': 'Identifiers', 'element_count': 1}]

        mock_execute_sql.side_effect = [
            mock_elements,
            mock_subjects,
            mock_categories
        ]
        mock_version.return_value = '1.0'

        tm = TaxonomyManager(mock_workspace_client)
        taxonomy = tm.get_active_taxonomy()

        # Verify structure
        assert 'elements' in taxonomy
        assert 'subjects' in taxonomy
        assert 'categories' in taxonomy
        assert taxonomy['total_elements'] == 1
        assert taxonomy['total_sensitive'] == 1
        assert taxonomy['version'] == '1.0'

    @patch.object(TaxonomyManager, '_execute_sql')
    @patch.object(TaxonomyManager, '_get_current_version')
    def test_get_active_taxonomy_counts_sensitive(
        self,
        mock_version,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should correctly count sensitive elements"""
        mock_elements = [
            {'element_id': '1', 'element_name': 'SSN', 'element_category': 'ID',
             'element_description': 'd', 'sensitive_flag': 'Yes', 'keywords': []},
            {'element_id': '2', 'element_name': 'Email', 'element_category': 'ID',
             'element_description': 'd', 'sensitive_flag': 'No', 'keywords': []},
            {'element_id': '3', 'element_name': 'CC', 'element_category': 'ID',
             'element_description': 'd', 'sensitive_flag': 'Yes', 'keywords': []}
        ]

        mock_execute_sql.side_effect = [
            mock_elements,
            [],  # subjects
            []   # categories
        ]
        mock_version.return_value = '1.0'

        tm = TaxonomyManager(mock_workspace_client)
        taxonomy = tm.get_active_taxonomy()

        assert taxonomy['total_sensitive'] == 2


class TestSQLExecution:
    """Test SQL execution logic"""

    def test_execute_sql_success(self, mock_workspace_client):
        """Should execute SQL and parse results"""
        # Setup mock response
        mock_col1 = Mock()
        mock_col1.name = "id"
        mock_col2 = Mock()
        mock_col2.name = "name"

        mock_statement = Mock()
        mock_statement.statement_id = "stmt-123"
        mock_statement.status.state = "SUCCEEDED"
        mock_statement.status.error = None
        mock_statement.result.data_array = [
            [1, "test1"],
            [2, "test2"]
        ]
        mock_statement.manifest.schema.columns = [mock_col1, mock_col2]

        mock_workspace_client.statement_execution.execute_statement.return_value = mock_statement

        tm = TaxonomyManager(mock_workspace_client)
        results = tm._execute_sql("SELECT * FROM test")

        # Verify results
        assert len(results) == 2
        assert results[0] == {'id': 1, 'name': 'test1'}
        assert results[1] == {'id': 2, 'name': 'test2'}

    def test_execute_sql_no_results(self, mock_workspace_client):
        """Should handle queries with no results"""
        mock_statement = Mock()
        mock_statement.statement_id = "stmt-123"
        mock_statement.status.state = "SUCCEEDED"
        mock_statement.status.error = None
        mock_statement.result = None

        mock_workspace_client.statement_execution.execute_statement.return_value = mock_statement

        tm = TaxonomyManager(mock_workspace_client)
        results = tm._execute_sql("UPDATE test SET x = 1")

        assert results == []

    def test_execute_sql_failure(self, mock_workspace_client):
        """Should raise exception on query failure"""
        mock_statement = Mock()
        mock_statement.statement_id = "stmt-123"
        mock_statement.status.state = "FAILED"
        mock_statement.status.error = "Syntax error"

        mock_workspace_client.statement_execution.execute_statement.return_value = mock_statement

        tm = TaxonomyManager(mock_workspace_client)

        with pytest.raises(Exception, match="Query failed"):
            tm._execute_sql("INVALID SQL")

    def test_execute_sql_waits_for_completion(self, mock_workspace_client):
        """Should wait for query completion"""
        # First call returns RUNNING, second returns SUCCEEDED
        mock_running = Mock()
        mock_running.statement_id = "stmt-123"
        mock_running.status.state = "RUNNING"

        mock_succeeded = Mock()
        mock_succeeded.statement_id = "stmt-123"
        mock_succeeded.status.state = "SUCCEEDED"
        mock_succeeded.result = None

        mock_workspace_client.statement_execution.execute_statement.return_value = mock_running
        mock_workspace_client.statement_execution.get_statement.return_value = mock_succeeded

        tm = TaxonomyManager(mock_workspace_client)
        with patch('time.sleep'):  # Mock sleep to avoid delays
            results = tm._execute_sql("SELECT * FROM test")

        # Should have called get_statement to check status
        assert mock_workspace_client.statement_execution.get_statement.called
