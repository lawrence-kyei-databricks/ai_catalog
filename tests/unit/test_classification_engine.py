"""
Unit tests for ClassificationEngine
Tests pattern matching, Claude API integration, auto-approval logic, caching, and fingerprinting
"""

import pytest
import json
import hashlib
from unittest.mock import Mock, patch, MagicMock
from classification_engine import ClassificationEngine, PatternRules


class TestClassificationEngineInit:
    """Test ClassificationEngine initialization"""

    def test_init_sets_dependencies(self, mock_workspace_client):
        """Should initialize with WorkspaceClient and TaxonomyManager"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        assert engine.w == mock_workspace_client
        assert engine.taxonomy_manager == mock_taxonomy_mgr

    def test_init_sets_model(self, mock_workspace_client):
        """Should set Claude model name"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        assert engine.model == "databricks-claude-3-7-sonnet"

    def test_init_sets_thresholds(self, mock_workspace_client):
        """Should set auto-approval thresholds"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        assert engine.TIER1_CONFIDENCE == 95
        assert engine.TIER2_CONFIDENCE == 85
        assert engine.PATTERN_MATCH_THRESHOLD == 0.8

    def test_init_creates_pattern_rules(self, mock_workspace_client):
        """Should create PatternRules instance"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        assert isinstance(engine.pattern_rules, PatternRules)


class TestGetColumnInfo:
    """Test column metadata retrieval"""

    @patch.object(ClassificationEngine, '_execute_sql')
    def test_get_column_info_success(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should retrieve column metadata and sample values"""
        mock_taxonomy_mgr = Mock()

        # Mock metadata query result
        metadata = [{'column_name': 'email', 'column_type': 'string'}]

        # Mock sample values query result
        samples = [
            {'value': 'test1@example.com'},
            {'value': 'test2@example.com'}
        ]

        mock_execute_sql.side_effect = [metadata, samples]

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine._get_column_info('main', 'schema1', 'table1', 'email')

        # Verify structure
        assert result['catalog'] == 'main'
        assert result['schema'] == 'schema1'
        assert result['table'] == 'table1'
        assert result['column_name'] == 'email'
        assert result['column_type'] == 'string'
        assert len(result['sample_values']) == 2
        assert result['full_name'] == 'main.schema1.table1.email'

    @patch.object(ClassificationEngine, '_execute_sql')
    def test_get_column_info_not_found(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should return None if column doesn't exist"""
        mock_taxonomy_mgr = Mock()
        mock_execute_sql.return_value = []  # No metadata found

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine._get_column_info('main', 'schema1', 'table1', 'nonexistent')

        assert result is None

    @patch.object(ClassificationEngine, '_execute_sql')
    def test_get_column_info_handles_sample_error(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should handle errors getting sample values gracefully"""
        mock_taxonomy_mgr = Mock()

        # Metadata succeeds, samples fail
        metadata = [{'column_name': 'email', 'column_type': 'string'}]
        mock_execute_sql.side_effect = [
            metadata,
            Exception("Sample query failed")
        ]

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine._get_column_info('main', 'schema1', 'table1', 'email')

        # Should still return column info with empty samples
        assert result is not None
        assert result['sample_values'] == []

    @patch.object(ClassificationEngine, '_execute_sql')
    def test_get_column_info_filters_null_samples(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should filter out None values from samples"""
        mock_taxonomy_mgr = Mock()

        metadata = [{'column_name': 'email', 'column_type': 'string'}]
        samples = [
            {'value': 'test@example.com'},
            {'value': None},
            {'value': 'valid@test.com'}
        ]

        mock_execute_sql.side_effect = [metadata, samples]

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine._get_column_info('main', 'schema1', 'table1', 'email')

        # Should only have non-null values
        assert len(result['sample_values']) == 2
        assert None not in result['sample_values']


class TestPatternDetection:
    """Test pattern detection in sample values"""

    def test_detect_pattern_ssn(self, mock_workspace_client):
        """Should detect SSN pattern"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        samples = ['123-45-6789', '987-65-4321', '555-12-3456']
        pattern = engine._detect_pattern(samples)

        assert pattern == 'ssn'

    def test_detect_pattern_email(self, mock_workspace_client):
        """Should detect email pattern"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        samples = ['test@example.com', 'user@domain.org', 'admin@company.net']
        pattern = engine._detect_pattern(samples)

        assert pattern == 'email'

    def test_detect_pattern_phone(self, mock_workspace_client):
        """Should detect phone pattern"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        samples = ['555-123-4567', '555-987-6543', '555-555-5555']
        pattern = engine._detect_pattern(samples)

        assert pattern == 'phone'

    def test_detect_pattern_credit_card(self, mock_workspace_client):
        """Should detect credit card pattern"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        samples = ['4532-1234-5678-9010', '5425-2334-3010-9903']
        pattern = engine._detect_pattern(samples)

        assert pattern == 'credit_card'

    def test_detect_pattern_date(self, mock_workspace_client):
        """Should detect date pattern"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        samples = ['2024-01-15', '2024-12-25', '2023-06-30']
        pattern = engine._detect_pattern(samples)

        assert pattern == 'date'

    def test_detect_pattern_uuid(self, mock_workspace_client):
        """Should detect UUID pattern"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        samples = [
            '550e8400-e29b-41d4-a716-446655440000',
            'f47ac10b-58cc-4372-a567-0e02b2c3d479'
        ]
        pattern = engine._detect_pattern(samples)

        assert pattern == 'uuid'

    def test_detect_pattern_requires_majority_match(self, mock_workspace_client):
        """Should require 70% match rate"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        # Only 50% match SSN pattern (2 out of 4)
        samples = ['123-45-6789', '987-65-4321', 'invalid', 'notassn']
        pattern = engine._detect_pattern(samples)

        assert pattern == 'unknown'

    def test_detect_pattern_empty_samples(self, mock_workspace_client):
        """Should handle empty sample list"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        pattern = engine._detect_pattern([])

        assert pattern == 'empty'


class TestFingerprintGeneration:
    """Test column fingerprint creation for caching"""

    def test_create_fingerprint_normalizes_name(self, mock_workspace_client):
        """Should normalize column name by removing numbers and special chars"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        column_info = {
            'column_name': 'email_addr_123',
            'column_type': 'string',
            'sample_values': []
        }

        fingerprint = engine._create_fingerprint(column_info)

        # Different column numbers should produce same fingerprint
        column_info2 = {
            'column_name': 'email_addr_456',
            'column_type': 'string',
            'sample_values': []
        }

        fingerprint2 = engine._create_fingerprint(column_info2)

        assert fingerprint == fingerprint2

    def test_create_fingerprint_includes_type(self, mock_workspace_client):
        """Should include column type in fingerprint"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        column_info1 = {
            'column_name': 'email',
            'column_type': 'string',
            'sample_values': []
        }

        column_info2 = {
            'column_name': 'email',
            'column_type': 'int',
            'sample_values': []
        }

        fp1 = engine._create_fingerprint(column_info1)
        fp2 = engine._create_fingerprint(column_info2)

        # Different types should produce different fingerprints
        assert fp1 != fp2

    def test_create_fingerprint_includes_pattern(self, mock_workspace_client):
        """Should include detected pattern in fingerprint"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        column_info1 = {
            'column_name': 'field',
            'column_type': 'string',
            'sample_values': ['test@example.com', 'user@domain.com']
        }

        column_info2 = {
            'column_name': 'field',
            'column_type': 'string',
            'sample_values': ['123-45-6789', '987-65-4321']
        }

        fp1 = engine._create_fingerprint(column_info1)
        fp2 = engine._create_fingerprint(column_info2)

        # Different patterns should produce different fingerprints
        assert fp1 != fp2

    def test_create_fingerprint_is_md5_hash(self, mock_workspace_client):
        """Should return MD5 hash"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        column_info = {
            'column_name': 'email',
            'column_type': 'string',
            'sample_values': []
        }

        fingerprint = engine._create_fingerprint(column_info)

        # MD5 hash should be 32 hex characters
        assert len(fingerprint) == 32
        assert all(c in '0123456789abcdef' for c in fingerprint)


class TestCacheLookup:
    """Test classification cache lookup"""

    @patch.object(ClassificationEngine, '_execute_sql')
    @patch.object(ClassificationEngine, '_create_fingerprint')
    def test_check_cache_hit(
        self,
        mock_fingerprint,
        mock_execute_sql,
        mock_workspace_client,
        sample_column_info
    ):
        """Should return cached result if found"""
        mock_taxonomy_mgr = Mock()
        mock_fingerprint.return_value = "abc123"

        cached_result = [{
            'element': 'Email Address',
            'category': 'Identifiers',
            'confidence': 90.0,
            'sensitive': False,
            'subjects': ['Associate', 'Consumer'],
            'reasoning': 'Previous classification'
        }]

        mock_execute_sql.return_value = cached_result

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine._check_cache(sample_column_info)

        # Should return cached result with slight confidence penalty
        assert result is not None
        assert result['element'] == 'Email Address'
        assert result['confidence'] == 90.0 * 0.95  # 5% penalty
        assert '[CACHED]' in result['reasoning']

    @patch.object(ClassificationEngine, '_execute_sql')
    @patch.object(ClassificationEngine, '_create_fingerprint')
    def test_check_cache_miss(
        self,
        mock_fingerprint,
        mock_execute_sql,
        mock_workspace_client,
        sample_column_info
    ):
        """Should return None if no cached result"""
        mock_taxonomy_mgr = Mock()
        mock_fingerprint.return_value = "abc123"
        mock_execute_sql.return_value = []  # No cached result

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine._check_cache(sample_column_info)

        assert result is None

    @patch.object(ClassificationEngine, '_execute_sql')
    @patch.object(ClassificationEngine, '_create_fingerprint')
    def test_check_cache_only_approved_statuses(
        self,
        mock_fingerprint,
        mock_execute_sql,
        mock_workspace_client,
        sample_column_info
    ):
        """Should only use approved/applied classifications"""
        mock_taxonomy_mgr = Mock()
        mock_fingerprint.return_value = "abc123"

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        engine._check_cache(sample_column_info)

        # Verify SQL query filters by status
        sql_call = mock_execute_sql.call_args[0][0]
        assert "AUTO_APPROVED" in sql_call
        assert "APPROVED" in sql_call
        assert "APPLIED" in sql_call


class TestClaudeAPIIntegration:
    """Test Claude API classification"""

    @patch.object(ClassificationEngine, '_execute_sql')
    def test_call_claude_api_success(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should call Claude API and parse JSON response"""
        mock_taxonomy_mgr = Mock()

        # Mock Claude API response
        claude_response = [{
            'result': json.dumps({
                'element': 'Email Address',
                'category': 'Identifiers',
                'confidence': 95.5,
                'sensitive': False,
                'subjects': ['Associate', 'Consumer'],
                'reasoning': 'Pattern match'
            })
        }]

        mock_execute_sql.return_value = claude_response

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine._call_claude_api("Test prompt")

        assert result['element'] == 'Email Address'
        assert result['confidence'] == 95.5

    @patch.object(ClassificationEngine, '_execute_sql')
    def test_call_claude_api_markdown_wrapped_json(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should extract JSON from markdown code blocks"""
        mock_taxonomy_mgr = Mock()

        # Claude sometimes wraps JSON in markdown
        claude_response = [{
            'result': '```json\n{"element": "Email Address", "confidence": 95}\n```'
        }]

        mock_execute_sql.return_value = claude_response

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine._call_claude_api("Test prompt")

        assert result['element'] == 'Email Address'
        assert result['confidence'] == 95

    @patch.object(ClassificationEngine, '_execute_sql')
    def test_call_claude_api_json_parse_error(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should handle JSON parse errors"""
        mock_taxonomy_mgr = Mock()

        claude_response = [{
            'result': 'This is not valid JSON'
        }]

        mock_execute_sql.return_value = claude_response

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine._call_claude_api("Test prompt")

        assert 'error' in result
        assert 'Invalid JSON' in result['error']

    @patch.object(ClassificationEngine, '_execute_sql')
    def test_call_claude_api_no_response(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should handle missing API response"""
        mock_taxonomy_mgr = Mock()
        mock_execute_sql.return_value = []

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine._call_claude_api("Test prompt")

        assert 'error' in result
        assert 'No response' in result['error']

    @patch.object(ClassificationEngine, '_execute_sql')
    def test_call_claude_api_escapes_prompt(
        self,
        mock_execute_sql,
        mock_workspace_client
    ):
        """Should escape quotes and backslashes in prompt"""
        mock_taxonomy_mgr = Mock()
        mock_execute_sql.return_value = []

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        engine._call_claude_api("Test with 'quotes' and \\backslash")

        # Verify SQL call has escaped characters
        sql_call = mock_execute_sql.call_args[0][0]
        assert "''" in sql_call or "\\\\" in sql_call


class TestBuildClassificationPrompt:
    """Test Claude prompt construction"""

    def test_build_prompt_includes_column_info(
        self,
        mock_workspace_client,
        sample_column_info,
        sample_taxonomy
    ):
        """Should include column metadata in prompt"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        prompt = engine._build_classification_prompt(sample_column_info, sample_taxonomy)

        assert sample_column_info['full_name'] in prompt
        assert sample_column_info['column_name'] in prompt
        assert sample_column_info['column_type'] in prompt

    def test_build_prompt_includes_sample_values(
        self,
        mock_workspace_client,
        sample_column_info,
        sample_taxonomy
    ):
        """Should include sample values in prompt"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        prompt = engine._build_classification_prompt(sample_column_info, sample_taxonomy)

        # Should show first 5 samples
        assert 'john.doe@example.com' in prompt

    def test_build_prompt_includes_taxonomy_elements(
        self,
        mock_workspace_client,
        sample_column_info,
        sample_taxonomy
    ):
        """Should include taxonomy elements grouped by category"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        prompt = engine._build_classification_prompt(sample_column_info, sample_taxonomy)

        assert 'Identifiers' in prompt
        assert 'Email Address' in prompt
        assert 'Social Security Number' in prompt

    def test_build_prompt_includes_subject_types(
        self,
        mock_workspace_client,
        sample_column_info,
        sample_taxonomy
    ):
        """Should include data subject types"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        prompt = engine._build_classification_prompt(sample_column_info, sample_taxonomy)

        assert 'Associate' in prompt
        assert 'B2B' in prompt
        assert 'Consumer' in prompt

    def test_build_prompt_marks_sensitive_elements(
        self,
        mock_workspace_client,
        sample_column_info,
        sample_taxonomy
    ):
        """Should mark sensitive elements in taxonomy"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        prompt = engine._build_classification_prompt(sample_column_info, sample_taxonomy)

        # SSN is sensitive, should have marker
        assert 'SENSITIVE' in prompt


class TestAutoApprovalDecision:
    """Test 3-tier auto-approval logic"""

    def test_auto_approval_tier1_high_confidence_pattern_match(
        self,
        mock_workspace_client
    ):
        """Tier 1: Should auto-approve with 95%+ confidence and pattern match"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        classification = {
            'confidence': 99.0,
            'sensitive': True,
            'pattern_match_score': 0.95
        }

        decision = engine._auto_approval_decision(classification)

        assert decision['review_status'] == 'AUTO_APPROVED'
        assert decision['approval_tier'] == 1
        assert decision['requires_review'] is False

    def test_auto_approval_tier2_good_confidence_non_sensitive(
        self,
        mock_workspace_client
    ):
        """Tier 2: Should auto-approve with 85%+ confidence if non-sensitive"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        classification = {
            'confidence': 88.0,
            'sensitive': False,
            'pattern_match_score': 0.5
        }

        decision = engine._auto_approval_decision(classification)

        assert decision['review_status'] == 'AUTO_APPROVED'
        assert decision['approval_tier'] == 2
        assert decision['requires_review'] is False

    def test_auto_approval_tier2_rejects_sensitive(
        self,
        mock_workspace_client
    ):
        """Tier 2: Should NOT auto-approve sensitive data"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        classification = {
            'confidence': 88.0,
            'sensitive': True,  # Sensitive requires tier 1
            'pattern_match_score': 0.5
        }

        decision = engine._auto_approval_decision(classification)

        assert decision['review_status'] == 'PENDING'
        assert decision['requires_review'] is True

    def test_auto_approval_tier3_low_confidence(
        self,
        mock_workspace_client
    ):
        """Tier 3: Should require review for low confidence"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        classification = {
            'confidence': 65.0,
            'sensitive': False,
            'pattern_match_score': 0.5
        }

        decision = engine._auto_approval_decision(classification)

        assert decision['review_status'] == 'PENDING'
        assert decision['approval_tier'] == 3
        assert decision['requires_review'] is True
        assert decision['review_priority'] in ['HIGH', 'MEDIUM', 'LOW']

    def test_calculate_priority_high_sensitive_low_confidence(
        self,
        mock_workspace_client
    ):
        """Should assign HIGH priority to sensitive data with low confidence"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        priority = engine._calculate_priority(confidence=65.0, sensitive=True)

        assert priority == 'HIGH'

    def test_calculate_priority_medium_sensitive_mid_confidence(
        self,
        mock_workspace_client
    ):
        """Should assign MEDIUM priority to sensitive data with mid confidence"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        priority = engine._calculate_priority(confidence=75.0, sensitive=True)

        assert priority == 'MEDIUM'

    def test_calculate_priority_low_non_sensitive(
        self,
        mock_workspace_client
    ):
        """Should assign LOW priority to non-sensitive data"""
        mock_taxonomy_mgr = Mock()
        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)

        priority = engine._calculate_priority(confidence=65.0, sensitive=False)

        assert priority == 'LOW'


class TestPatternRules:
    """Test PatternRules class for pattern-based classification"""

    def test_pattern_rules_ssn_match(self, sample_ssn_data):
        """Should match SSN pattern"""
        rules = PatternRules()

        result = rules.check_pattern(
            sample_ssn_data['column_name'],
            sample_ssn_data['sample_values']
        )

        assert result is not None
        assert result['element'] == 'Social Security Number'
        assert result['category'] == 'Identifiers'
        assert result['confidence'] == 99.0
        assert result['sensitive'] is True

    def test_pattern_rules_email_match(self, sample_email_data):
        """Should match email pattern"""
        rules = PatternRules()

        result = rules.check_pattern(
            sample_email_data['column_name'],
            sample_email_data['sample_values']
        )

        assert result is not None
        assert result['element'] == 'Email Address'
        assert result['sensitive'] is False

    def test_pattern_rules_phone_match(self, sample_phone_data):
        """Should match phone pattern"""
        rules = PatternRules()

        result = rules.check_pattern(
            sample_phone_data['column_name'],
            sample_phone_data['sample_values']
        )

        assert result is not None
        assert result['element'] == 'Phone Number'

    def test_pattern_rules_credit_card_match(self, sample_credit_card_data):
        """Should match credit card pattern"""
        rules = PatternRules()

        result = rules.check_pattern(
            sample_credit_card_data['column_name'],
            sample_credit_card_data['sample_values']
        )

        assert result is not None
        assert result['element'] == 'Credit Card / Debit Card Number'
        assert result['category'] == 'Payment Card Info'
        assert result['sensitive'] is True

    def test_pattern_rules_requires_column_name_match(self):
        """Should require column name to match pattern keywords"""
        rules = PatternRules()

        # Email pattern data but wrong column name
        result = rules.check_pattern(
            'random_field',
            ['test@example.com', 'user@domain.com']
        )

        assert result is None

    def test_pattern_rules_requires_80_percent_match(self):
        """Should require 80% of samples to match pattern"""
        rules = PatternRules()

        # Only 50% match (1 out of 2)
        result = rules.check_pattern(
            'customer_ssn',
            ['123-45-6789', 'invalid_value']
        )

        assert result is None

    def test_pattern_rules_includes_match_score(self, sample_ssn_data):
        """Should include pattern match score in result"""
        rules = PatternRules()

        result = rules.check_pattern(
            sample_ssn_data['column_name'],
            sample_ssn_data['sample_values']
        )

        assert 'pattern_match_score' in result
        assert result['pattern_match_score'] == 1.0  # 100% match

    def test_pattern_rules_no_samples(self):
        """Should return None if no sample values"""
        rules = PatternRules()

        result = rules.check_pattern('customer_ssn', [])

        assert result is None


class TestClassifyColumn:
    """Test end-to-end column classification"""

    @patch.object(ClassificationEngine, '_get_column_info')
    def test_classify_column_not_found(
        self,
        mock_get_column_info,
        mock_workspace_client
    ):
        """Should return error if column not found"""
        mock_taxonomy_mgr = Mock()
        mock_get_column_info.return_value = None

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine.classify_column('main', 'schema1', 'table1', 'nonexistent')

        assert 'error' in result
        assert result['error'] == 'Column not found'

    @patch.object(ClassificationEngine, '_get_column_info')
    @patch.object(ClassificationEngine, '_finalize_classification')
    @patch.object(PatternRules, 'check_pattern')
    def test_classify_column_pattern_match_first(
        self,
        mock_pattern_check,
        mock_finalize,
        mock_get_column_info,
        mock_workspace_client,
        sample_column_info
    ):
        """Should check pattern rules first (fastest path)"""
        mock_taxonomy_mgr = Mock()
        mock_get_column_info.return_value = sample_column_info

        pattern_result = {
            'element': 'Email Address',
            'confidence': 99.0
        }
        mock_pattern_check.return_value = pattern_result
        mock_finalize.return_value = {'final': 'result'}

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine.classify_column('main', 'schema1', 'table1', 'email')

        # Should finalize with pattern result
        mock_finalize.assert_called_once_with(
            sample_column_info,
            pattern_result,
            'PATTERN_RULE'
        )

    @patch.object(ClassificationEngine, '_get_column_info')
    @patch.object(ClassificationEngine, '_check_cache')
    @patch.object(ClassificationEngine, '_finalize_classification')
    @patch.object(PatternRules, 'check_pattern')
    def test_classify_column_cache_second(
        self,
        mock_pattern_check,
        mock_finalize,
        mock_check_cache,
        mock_get_column_info,
        mock_workspace_client,
        sample_column_info
    ):
        """Should check cache if no pattern match"""
        mock_taxonomy_mgr = Mock()
        mock_get_column_info.return_value = sample_column_info
        mock_pattern_check.return_value = None  # No pattern match

        cache_result = {
            'element': 'Cached Element',
            'confidence': 85.5
        }
        mock_check_cache.return_value = cache_result
        mock_finalize.return_value = {'final': 'result'}

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine.classify_column('main', 'schema1', 'table1', 'field')

        # Should finalize with cached result
        mock_finalize.assert_called_once_with(
            sample_column_info,
            cache_result,
            'CACHE'
        )

    @patch.object(ClassificationEngine, '_get_column_info')
    @patch.object(ClassificationEngine, '_check_cache')
    @patch.object(ClassificationEngine, '_classify_with_claude')
    @patch.object(ClassificationEngine, '_finalize_classification')
    @patch.object(PatternRules, 'check_pattern')
    def test_classify_column_claude_last(
        self,
        mock_pattern_check,
        mock_finalize,
        mock_classify_claude,
        mock_check_cache,
        mock_get_column_info,
        mock_workspace_client,
        sample_column_info
    ):
        """Should use Claude if no pattern match or cache hit"""
        mock_taxonomy_mgr = Mock()
        mock_get_column_info.return_value = sample_column_info
        mock_pattern_check.return_value = None  # No pattern
        mock_check_cache.return_value = None  # No cache

        ai_result = {
            'element': 'AI Classified',
            'confidence': 92.0
        }
        mock_classify_claude.return_value = ai_result
        mock_finalize.return_value = {'final': 'result'}

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        result = engine.classify_column('main', 'schema1', 'table1', 'field')

        # Should finalize with Claude result
        mock_finalize.assert_called_once_with(
            sample_column_info,
            ai_result,
            'CLAUDE'
        )


class TestStoreClassification:
    """Test storing classification results"""

    @patch.object(ClassificationEngine, '_execute_sql')
    @patch.object(ClassificationEngine, '_create_fingerprint')
    def test_store_classification_creates_merge(
        self,
        mock_fingerprint,
        mock_execute_sql,
        mock_workspace_client,
        sample_column_info
    ):
        """Should create MERGE statement to store classification"""
        mock_taxonomy_mgr = Mock()
        mock_fingerprint.return_value = "abc123"
        mock_execute_sql.return_value = []

        result = {
            'element': 'Email Address',
            'category': 'Identifiers',
            'confidence': 95.0,
            'sensitive': False,
            'subjects': ['Associate'],
            'reasoning': 'Test',
            'review_status': 'AUTO_APPROVED',
            'approval_tier': 1,
            'requires_review': False,
            'review_priority': None,
            'classification_source': 'CLAUDE'
        }

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        engine._store_classification(sample_column_info, result)

        # Verify SQL was called
        assert mock_execute_sql.called
        sql_call = mock_execute_sql.call_args[0][0]
        assert "MERGE INTO" in sql_call
        assert "classification_governance" in sql_call
        assert "Email Address" in sql_call

    @patch.object(ClassificationEngine, '_execute_sql')
    @patch.object(ClassificationEngine, '_create_fingerprint')
    def test_store_classification_includes_all_fields(
        self,
        mock_fingerprint,
        mock_execute_sql,
        mock_workspace_client,
        sample_column_info
    ):
        """Should include all classification fields in storage"""
        mock_taxonomy_mgr = Mock()
        mock_fingerprint.return_value = "abc123"
        mock_execute_sql.return_value = []

        result = {
            'element': 'Test',
            'category': 'Cat',
            'confidence': 90.0,
            'sensitive': True,
            'subjects': ['Consumer'],
            'reasoning': 'Reason',
            'review_status': 'PENDING',
            'approval_tier': 3,
            'requires_review': True,
            'review_priority': 'HIGH',
            'classification_source': 'PATTERN_RULE'
        }

        engine = ClassificationEngine(mock_workspace_client, mock_taxonomy_mgr)
        engine._store_classification(sample_column_info, result)

        sql_call = mock_execute_sql.call_args[0][0]

        # Verify key fields are in SQL
        assert 'confidence_score = 90.0' in sql_call
        assert 'sensitive_flag = true' in sql_call
        assert "review_status = 'PENDING'" in sql_call
        assert 'approval_tier = 3' in sql_call
