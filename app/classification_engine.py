"""
CarMax Data Classification Platform
Classification Engine - Claude 3.7 Sonnet with Smart Auto-Approval

This module handles:
- Column classification using Claude 3.7
- Pattern-based classification
- Native UC classification integration
- Smart auto-approval (3-tier system)
- Confidence scoring
"""

import json
import re
import hashlib
import time
import os
from typing import Dict, List, Optional
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from .taxonomy_manager import TaxonomyManager


class ClassificationEngine:
    """
    AI-powered classification engine with smart auto-approval
    """

    def __init__(self, w: WorkspaceClient, taxonomy_manager: TaxonomyManager):
        self.w = w
        self.taxonomy_manager = taxonomy_manager
        self.warehouse_id = os.environ.get('WAREHOUSE_ID')
        self.model = os.environ.get('MODEL_ENDPOINT', 'databricks-claude-3-7-sonnet')

        # Use environment variable for schema name, defaulting to carmax for backward compatibility
        org_name = os.environ.get('ORG_NAME', 'carmax')
        catalog = os.environ.get('TARGET_CATALOG', 'main')
        self.governance_schema = f"{catalog}.{org_name}_governance"

        # Auto-approval thresholds
        self.TIER1_CONFIDENCE = 95  # Auto-approve immediately
        self.TIER2_CONFIDENCE = 85  # Conditional auto-approve
        self.PATTERN_MATCH_THRESHOLD = 0.8

        # Pattern rules for common PII
        self.pattern_rules = PatternRules()

    def classify_column(self, catalog: str, schema: str, table: str, column: str) -> Dict:
        """
        Classify a single column with smart auto-approval

        Returns:
            Classification result with approval decision
        """

        print(f"[ClassificationEngine] Classifying {catalog}.{schema}.{table}.{column}")

        # 1. Get column metadata + samples
        column_info = self._get_column_info(catalog, schema, table, column)

        if not column_info:
            return {'error': 'Column not found'}

        # 2. Check pattern rules first (fastest)
        pattern_result = self.pattern_rules.check_pattern(
            column_info['column_name'],
            column_info.get('sample_values', [])
        )

        if pattern_result:
            print(f"[ClassificationEngine] ✓ Pattern match: {pattern_result['element']}")
            return self._finalize_classification(column_info, pattern_result, 'PATTERN_RULE')

        # 3. Check cache (previously classified similar columns)
        cache_result = self._check_cache(column_info)

        if cache_result:
            print(f"[ClassificationEngine] ✓ Cache hit: {cache_result['element']}")
            return self._finalize_classification(column_info, cache_result, 'CACHE')

        # 4. Use Claude 3.7 for AI classification
        ai_result = self._classify_with_claude(column_info)

        return self._finalize_classification(column_info, ai_result, 'CLAUDE')

    def _get_column_info(self, catalog: str, schema: str, table: str, column: str) -> Optional[Dict]:
        """Get column metadata and sample values"""

        try:
            # Get column metadata
            metadata_query = f"""
            SELECT
              column_name,
              data_type as column_type
            FROM system.information_schema.columns
            WHERE table_catalog = '{catalog}'
              AND table_schema = '{schema}'
              AND table_name = '{table}'
              AND column_name = '{column}'
            """

            metadata = self._execute_sql(metadata_query)

            if not metadata:
                return None

            # Get sample values (up to 10 non-null, distinct values)
            sample_query = f"""
            SELECT DISTINCT `{column}` as value
            FROM `{catalog}`.`{schema}`.`{table}`
            WHERE `{column}` IS NOT NULL
            LIMIT 10
            """

            try:
                samples = self._execute_sql(sample_query)
                sample_values = [str(s['value']) for s in samples if s['value'] is not None]
            except:
                sample_values = []

            return {
                'catalog': catalog,
                'schema': schema,
                'table': table,
                'column_name': column,
                'column_type': metadata[0]['column_type'],
                'sample_values': sample_values,
                'full_name': f"{catalog}.{schema}.{table}.{column}"
            }

        except Exception as e:
            print(f"[ClassificationEngine] Error getting column info: {e}")
            return None

    def _classify_with_claude(self, column_info: Dict) -> Dict:
        """Classify using Claude 3.7 Sonnet"""

        # Get current taxonomy
        taxonomy = self.taxonomy_manager.get_active_taxonomy()

        # Build prompt
        prompt = self._build_classification_prompt(column_info, taxonomy)

        # Call Claude
        result = self._call_claude_api(prompt)

        return result

    def _build_classification_prompt(self, column_info: Dict, taxonomy: Dict) -> str:
        """Build dynamic classification prompt"""

        # Group elements by category
        by_category = {}
        for elem in taxonomy['elements']:
            cat = elem['element_category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(elem)

        # Format taxonomy
        taxonomy_text = ""
        for category, elements in sorted(by_category.items()):
            taxonomy_text += f"\n### {category} ({len(elements)} elements)\n"
            for elem in elements[:10]:  # Show first 10 per category for brevity
                sensitive = "🔒 SENSITIVE" if elem['sensitive_flag'] == 'Yes' else ""
                taxonomy_text += f"  - {elem['element_name']} {sensitive}\n"
            if len(elements) > 10:
                taxonomy_text += f"  ... and {len(elements) - 10} more\n"

        # Build prompt
        prompt = f"""You are classifying data for CarMax automotive retail company.

COLUMN TO CLASSIFY:
- Full Path: {column_info['full_name']}
- Column Name: {column_info['column_name']}
- Data Type: {column_info['column_type']}
- Sample Values: {json.dumps(column_info['sample_values'][:5])}

CARMAX CLASSIFICATION TAXONOMY ({taxonomy['total_elements']} elements):
{taxonomy_text}

DATA SUBJECT TYPES (who does this data belong to?):
- Associate: Internal personnel (employees, contractors)
- B2B: External business contacts (vendors, partners)
- Consumer: Individual customers

TASK:
1. Analyze the column name, data type, and sample values
2. Determine which CarMax data element best matches this column
3. Assess if it contains sensitive/PII data
4. Identify applicable data subject types
5. Provide confidence score (0-100)
6. Explain your reasoning

IMPORTANT:
- Be precise: choose the EXACT element name from the taxonomy
- Be confident: only return 90%+ confidence if you're certain
- Consider context: this is automotive retail (vehicle sales, financing, service)
- Flag sensitive data: SSN, credit cards, medical, biometrics are all sensitive

Return ONLY valid JSON in this exact format:
{{
  "element": "exact element name from taxonomy",
  "category": "exact category name",
  "confidence": 85.5,
  "sensitive": true,
  "subjects": ["Associate", "Consumer"],
  "reasoning": "Column name 'ssn' and sample pattern XXX-XX-XXXX clearly indicates Social Security Number"
}}"""

        return prompt

    def _call_claude_api(self, prompt: str) -> Dict:
        """Call Claude 3.7 via Databricks Foundation Model API"""

        escaped_prompt = prompt.replace("'", "''").replace("\\", "\\\\")

        query = f"""
        SELECT ai_query(
          '{self.model}',
          '{escaped_prompt}'
        ) as result
        """

        try:
            result = self._execute_sql(query)

            if result and result[0].get('result'):
                # Parse JSON response
                response_text = result[0]['result']

                # Extract JSON (Claude sometimes wraps in markdown)
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    classification = json.loads(json_match.group())
                else:
                    classification = json.loads(response_text)

                return classification

            return {'error': 'No response from Claude'}

        except json.JSONDecodeError as e:
            print(f"[ClassificationEngine] JSON parse error: {e}")
            return {'error': f'Invalid JSON response: {e}'}
        except Exception as e:
            print(f"[ClassificationEngine] Claude API error: {e}")
            return {'error': str(e)}

    def _check_cache(self, column_info: Dict) -> Optional[Dict]:
        """Check if similar column was classified before"""

        fingerprint = self._create_fingerprint(column_info)

        query = f"""
        SELECT
          suggested_element as element,
          suggested_category as category,
          confidence_score as confidence,
          sensitive_flag as sensitive,
          data_subjects as subjects,
          reasoning
        FROM {self.governance_schema}.classification_governance
        WHERE column_fingerprint = '{fingerprint}'
          AND review_status IN ('AUTO_APPROVED', 'APPROVED', 'APPLIED')
        LIMIT 1
        """

        results = self._execute_sql(query)

        if results:
            cached = results[0]
            # Slight confidence penalty for cached results
            cached['confidence'] = float(cached['confidence']) * 0.95
            cached['reasoning'] = f"[CACHED] {cached['reasoning']}"
            return cached

        return None

    def _create_fingerprint(self, column_info: Dict) -> str:
        """Create fingerprint for caching similar columns"""

        # Normalize column name
        normalized_name = re.sub(r'[0-9_-]', '', column_info['column_name'].lower())

        # Detect pattern from samples
        pattern = self._detect_pattern(column_info.get('sample_values', []))

        # Fingerprint = hash(name + type + pattern)
        fingerprint_str = f"{normalized_name}|{column_info['column_type']}|{pattern}"
        return hashlib.md5(fingerprint_str.encode()).hexdigest()

    def _detect_pattern(self, sample_values: List[str]) -> str:
        """Detect common pattern in sample values"""

        if not sample_values:
            return 'empty'

        # Check for common patterns
        patterns = {
            'ssn': r'^\d{3}-\d{2}-\d{4}$',
            'email': r'^[\w\.-]+@[\w\.-]+\.\w+$',
            'phone': r'^\d{3}-\d{3}-\d{4}$',
            'credit_card': r'^\d{4}-\d{4}-\d{4}-\d{4}$',
            'date': r'^\d{4}-\d{2}-\d{2}$',
            'uuid': r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
        }

        for pattern_name, regex in patterns.items():
            matches = sum(1 for v in sample_values if re.match(regex, str(v), re.IGNORECASE))
            if matches / len(sample_values) > 0.7:
                return pattern_name

        return 'unknown'

    def _finalize_classification(self, column_info: Dict, classification: Dict,
                                 source: str) -> Dict:
        """
        Finalize classification with auto-approval decision
        """

        # Validate element exists in taxonomy
        element = classification.get('element', '')
        if not element or element.lower() in ['no matching element', 'no match', 'none', 'unknown']:
            classification['element'] = 'No matching element'
            classification['confidence'] = 0
            # Force manual review
            approval_decision = {
                'review_status': 'PENDING',
                'approval_tier': 3,
                'requires_review': True,
                'review_priority': 'LOW',
                'review_reasons': ['No matching taxonomy element found']
            }
        else:
            # Apply auto-approval logic
            approval_decision = self._auto_approval_decision(classification)

        # Create final result
        final_result = {
            **classification,
            'column_info': column_info,
            'classification_source': source,
            **approval_decision
        }

        # Store in governance table
        self._store_classification(column_info, final_result)

        return final_result

    def _auto_approval_decision(self, classification: Dict) -> Dict:
        """
        Smart auto-approval: 3-tier system

        Tier 1: Auto-approve (95%+ confidence + pattern match)
        Tier 2: Conditional auto-approve (85%+ confidence, non-sensitive)
        Tier 3: Human review required
        """

        confidence = classification.get('confidence', 0)
        sensitive = classification.get('sensitive', False)
        pattern_match = classification.get('pattern_match_score', 0)

        # TIER 1: Auto-approve (highest confidence)
        if confidence >= self.TIER1_CONFIDENCE and pattern_match >= self.PATTERN_MATCH_THRESHOLD:
            return {
                'review_status': 'AUTO_APPROVED',
                'approval_tier': 1,
                'requires_review': False,
                'review_priority': None,
                'approval_reason': f'High confidence ({confidence}%) + pattern match'
            }

        # TIER 2: Conditional auto-approve
        if confidence >= self.TIER2_CONFIDENCE and not sensitive:
            return {
                'review_status': 'AUTO_APPROVED',
                'approval_tier': 2,
                'requires_review': False,
                'review_priority': None,
                'approval_reason': f'Good confidence ({confidence}%), non-sensitive'
            }

        # TIER 3: Human review required
        reasons = []
        if confidence < self.TIER2_CONFIDENCE:
            reasons.append(f'Confidence below threshold ({confidence}% < 85%)')
        if sensitive and confidence < self.TIER1_CONFIDENCE:
            reasons.append('Sensitive data requires high confidence')
        if pattern_match < self.PATTERN_MATCH_THRESHOLD:
            reasons.append('Pattern mismatch')

        priority = self._calculate_priority(confidence, sensitive)

        return {
            'review_status': 'PENDING',
            'approval_tier': 3,
            'requires_review': True,
            'review_priority': priority,
            'review_reasons': reasons
        }

    def _calculate_priority(self, confidence: float, sensitive: bool) -> str:
        """Calculate review priority"""

        if sensitive and confidence < 70:
            return 'HIGH'
        elif sensitive and confidence < 85:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _store_classification(self, column_info: Dict, result: Dict):
        """Store classification in governance table"""

        fingerprint = self._create_fingerprint(column_info)
        subjects_array = json.dumps(result.get('subjects', []))
        samples_json = json.dumps(column_info.get('sample_values', []))

        sql = f"""
        MERGE INTO {self.governance_schema}.classification_governance AS target
        USING (
          SELECT
            '{column_info['catalog']}' as catalog_name,
            '{column_info['schema']}' as schema_name,
            '{column_info['table']}' as table_name,
            '{column_info['column_name']}' as column_name
        ) AS source
        ON target.catalog_name = source.catalog_name
          AND target.schema_name = source.schema_name
          AND target.table_name = source.table_name
          AND target.column_name = source.column_name
        WHEN MATCHED THEN
          UPDATE SET
            column_type = '{column_info['column_type']}',
            suggested_element = {self._quote(result.get('element'))},
            suggested_category = {self._quote(result.get('category'))},
            confidence_score = {result.get('confidence', 0)},
            sensitive_flag = {str(result.get('sensitive', False)).lower()},
            data_subjects = from_json('{subjects_array}', 'array<string>'),
            reasoning = {self._quote(result.get('reasoning', ''))},
            review_status = '{result.get('review_status', 'PENDING')}',
            approval_tier = {result.get('approval_tier', 3)},
            requires_review = {str(result.get('requires_review', True)).lower()},
            review_priority = {self._quote(result.get('review_priority'))},
            classification_source = '{result.get('classification_source', 'CLAUDE')}',
            model_used = '{self.model}',
            sample_values = '{samples_json.replace("'", "''")}',
            column_fingerprint = '{fingerprint}',
            created_at = current_timestamp()
        WHEN NOT MATCHED THEN
          INSERT (catalog_name, schema_name, table_name, column_name, column_type,
                 suggested_element, suggested_category, confidence_score, sensitive_flag,
                 data_subjects, reasoning, review_status, approval_tier, requires_review,
                 review_priority, classification_source, model_used, sample_values,
                 column_fingerprint)
          VALUES ('{column_info['catalog']}', '{column_info['schema']}',
                 '{column_info['table']}', '{column_info['column_name']}',
                 '{column_info['column_type']}',
                 {self._quote(result.get('element'))}, {self._quote(result.get('category'))},
                 {result.get('confidence', 0)}, {str(result.get('sensitive', False)).lower()},
                 from_json('{subjects_array}', 'array<string>'),
                 {self._quote(result.get('reasoning', ''))},
                 '{result.get('review_status', 'PENDING')}', {result.get('approval_tier', 3)},
                 {str(result.get('requires_review', True)).lower()},
                 {self._quote(result.get('review_priority'))},
                 '{result.get('classification_source', 'CLAUDE')}', '{self.model}',
                 '{samples_json.replace("'", "''")}', '{fingerprint}')
        """

        self._execute_sql(sql)

    def _execute_sql(self, sql: str) -> List[Dict]:
        """Execute SQL and return results"""
        try:
            statement = self.w.statement_execution.execute_statement(
                statement=sql,
                warehouse_id=self.warehouse_id,
                wait_timeout="50s"
            )

            # Wait for completion
            import time
            while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
                time.sleep(1)
                statement = self.w.statement_execution.get_statement(statement.statement_id)

            # Check for errors
            if statement.status.state == StatementState.FAILED:
                raise Exception(f"SQL execution failed: {statement.status.error.message if statement.status.error else 'Unknown error'}")

            # Parse results
            if hasattr(statement, 'result') and statement.result:
                columns = [col.name for col in statement.manifest.schema.columns] if statement.manifest else []
                data_array = statement.result.data_array if statement.result.data_array else []
                return [dict(zip(columns, row)) for row in data_array]

            return []

        except Exception as e:
            print(f"[ClassificationEngine] SQL Error: {e}")
            raise

    def _quote(self, value) -> str:
        """SQL quote helper"""
        if value is None:
            return 'NULL'
        return "'" + str(value).replace("'", "''") + "'"


class PatternRules:
    """
    Pattern-based classification rules for common PII
    """

    RULES = [
        {
            'pattern': r'^\d{3}-\d{2}-\d{4}$',
            'column_patterns': ['ssn', 'social_security', 'social_sec'],
            'element': 'Social Security Number',
            'category': 'Identifiers',
            'sensitive': True,
            'confidence': 99.0
        },
        {
            'pattern': r'^[\w\.-]+@[\w\.-]+\.\w+$',
            'column_patterns': ['email', 'e_mail', 'email_addr'],
            'element': 'Email Address',
            'category': 'Identifiers',
            'sensitive': False,
            'confidence': 99.0
        },
        {
            'pattern': r'^\d{3}-\d{3}-\d{4}$',
            'column_patterns': ['phone', 'telephone', 'mobile', 'cell'],
            'element': 'Phone Number',
            'category': 'Identifiers',
            'sensitive': False,
            'confidence': 99.0
        },
        {
            'pattern': r'^\d{4}-?\d{4}-?\d{4}-?\d{4}$',
            'column_patterns': ['credit_card', 'cc', 'card_num'],
            'element': 'Credit Card / Debit Card Number',
            'category': 'Payment Card Info',
            'sensitive': True,
            'confidence': 99.0
        },
    ]

    def check_pattern(self, column_name: str, sample_values: List[str]) -> Optional[Dict]:
        """Check if column matches any pattern rules"""

        for rule in self.RULES:
            # Check column name
            name_match = any(
                pattern in column_name.lower()
                for pattern in rule['column_patterns']
            )

            if not name_match:
                continue

            # Check sample values
            if not sample_values:
                continue

            matches = sum(
                1 for val in sample_values
                if re.match(rule['pattern'], str(val))
            )

            match_ratio = matches / len(sample_values) if sample_values else 0

            if match_ratio >= 0.8:  # 80% match
                return {
                    'element': rule['element'],
                    'category': rule['category'],
                    'confidence': rule['confidence'],
                    'sensitive': rule['sensitive'],
                    'pattern_match_score': match_ratio,
                    'subjects': ['Associate', 'Consumer'],  # Default
                    'reasoning': f'Pattern match: {match_ratio*100:.0f}% samples match {rule["pattern"]}'
                }

        return None
