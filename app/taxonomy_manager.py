"""
CarMax Data Classification Platform
Taxonomy Manager - Load and manage CarMax 172-element taxonomy

This module handles:
- Import from Excel files
- CRUD operations on data elements
- Versioning and change tracking
- UC tag synchronization
"""

import pandas as pd
import json
import hashlib
import re
import os
from typing import Dict, List, Optional
from datetime import datetime
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState


class TaxonomyManager:
    """
    Manage CarMax data classification taxonomy lifecycle
    """

    def __init__(self, w: WorkspaceClient, warehouse_id: str = None):
        self.w = w
        self.warehouse_id = warehouse_id or os.environ.get('WAREHOUSE_ID')
        self.taxonomy_schema = "main.carmax_taxonomy"
        self.tags_schema = "main.carmax_tags"

    def import_from_excel(self,
                          elements_file: str,
                          subjects_file: str,
                          version: str = "1.0") -> Dict:
        """
        Load CarMax taxonomy from Excel files into database

        Args:
            elements_file: Path to Data_Element_Descriptions.xlsx
            subjects_file: Path to Personal Data Excel
            version: Version number for this import

        Returns:
            Import summary dict
        """

        print(f"[TaxonomyManager] Starting import version {version}")

        # 1. Read Excel files
        elements_df = pd.read_excel(elements_file)
        subjects_df = pd.read_excel(subjects_file)

        print(f"[TaxonomyManager] Loaded {len(elements_df)} elements, {len(subjects_df)} subject types")

        # 2. Load Data Elements (172 rows)
        loaded_count = self._import_elements(elements_df)

        # 3. Load Subject Types (3 rows)
        self._import_subjects(subjects_df)

        # 4. Update categories
        self._update_categories(elements_df)

        # 5. Create version record
        self._create_version_record(version, loaded_count, 'INITIAL',
                                    'Imported CarMax taxonomy from Excel')

        # 6. Sync UC tags
        tags_created = self._sync_uc_tags()

        print(f"[TaxonomyManager] ✓ Import complete: {loaded_count} elements, {tags_created} tags")

        return {
            'elements_imported': loaded_count,
            'subjects_imported': len(subjects_df),
            'tags_created': tags_created,
            'version': version,
            'timestamp': datetime.now().isoformat()
        }

    def _import_elements(self, elements_df: pd.DataFrame) -> int:
        """Import data elements from DataFrame"""

        loaded = 0

        for _, row in elements_df.iterrows():
            element_id = self._generate_element_id(row['Data Element Name'])
            element_name = row['Data Element Name']

            # Extract keywords
            keywords = self._extract_keywords(element_name)
            keywords_sql = f"array({', '.join([self._quote(k) for k in keywords])})"

            sql = f"""
            MERGE INTO {self.taxonomy_schema}.data_elements AS target
            USING (
              SELECT
                '{element_id}' as element_id,
                {self._quote(element_name)} as element_name,
                {self._quote(row['Data Category'])} as element_category,
                {self._quote(str(row.get('Description', '')))} as element_description,
                '{row['Sensitive_Flag']}' as sensitive_flag,
                {self._quote(str(row.get('Data Classification', '')))} as data_classification,
                {keywords_sql} as keywords
            ) AS source
            ON target.element_id = source.element_id
            WHEN MATCHED THEN
              UPDATE SET
                element_name = source.element_name,
                element_category = source.element_category,
                element_description = source.element_description,
                sensitive_flag = source.sensitive_flag,
                data_classification = source.data_classification,
                keywords = source.keywords,
                updated_at = current_timestamp()
            WHEN NOT MATCHED THEN
              INSERT (element_id, element_name, element_category, element_description,
                     sensitive_flag, data_classification, keywords)
              VALUES (source.element_id, source.element_name, source.element_category,
                     source.element_description, source.sensitive_flag,
                     source.data_classification, source.keywords)
            """

            try:
                self._execute_sql(sql)
                loaded += 1
            except Exception as e:
                print(f"[TaxonomyManager] Error loading element '{element_name}': {e}")

        return loaded

    def _import_subjects(self, subjects_df: pd.DataFrame):
        """Import subject types from DataFrame"""

        for _, row in subjects_df.iterrows():
            sql = f"""
            MERGE INTO {self.taxonomy_schema}.subject_types AS target
            USING (
              SELECT
                '{row['Data Subject Type Id']}' as subject_type_id,
                '{row['Data Subject Type Name']}' as subject_type_name,
                {self._quote(row['Description'])} as subject_description
            ) AS source
            ON target.subject_type_id = source.subject_type_id
            WHEN MATCHED THEN
              UPDATE SET
                subject_type_name = source.subject_type_name,
                subject_description = source.subject_description
            WHEN NOT MATCHED THEN
              INSERT (subject_type_id, subject_type_name, subject_description)
              VALUES (source.subject_type_id, source.subject_type_name,
                     source.subject_description)
            """

            self._execute_sql(sql)

    def _update_categories(self, elements_df: pd.DataFrame):
        """Extract and update unique categories"""

        categories = elements_df['Data Category'].value_counts().to_dict()

        for category_name, count in categories.items():
            category_id = self._generate_element_id(category_name)

            sql = f"""
            MERGE INTO {self.taxonomy_schema}.data_categories AS target
            USING (
              SELECT
                '{category_id}' as category_id,
                {self._quote(category_name)} as category_name,
                {count} as element_count
            ) AS source
            ON target.category_id = source.category_id
            WHEN MATCHED THEN
              UPDATE SET element_count = source.element_count
            WHEN NOT MATCHED THEN
              INSERT (category_id, category_name, element_count)
              VALUES (source.category_id, source.category_name, source.element_count)
            """

            self._execute_sql(sql)

    def _sync_uc_tags(self) -> int:
        """Create Unity Catalog tags for all 172 data elements"""

        # Get all active elements
        elements = self._execute_sql(f"""
            SELECT element_id, element_name, element_description
            FROM {self.taxonomy_schema}.data_elements
            WHERE active = TRUE
        """)

        tags_created = 0

        for elem in elements:
            tag_name = elem['element_id']
            description = elem.get('element_description', elem['element_name'])

            # Create tag (idempotent)
            sql = f"""
            CREATE TAG IF NOT EXISTS {self.tags_schema}.`{tag_name}`
            """

            try:
                self._execute_sql(sql)

                # Add comment to tag
                comment_sql = f"""
                COMMENT ON TAG {self.tags_schema}.`{tag_name}`
                IS {self._quote(description)}
                """
                self._execute_sql(comment_sql)

                tags_created += 1
            except Exception as e:
                print(f"[TaxonomyManager] Warning: Could not create tag {tag_name}: {e}")

        return tags_created

    def get_active_taxonomy(self) -> Dict:
        """
        Get current active taxonomy for classification engine

        Returns:
            Dict with elements, subjects, version info
        """

        elements = self._execute_sql(f"""
            SELECT
              element_id,
              element_name,
              element_category,
              element_description,
              sensitive_flag,
              keywords
            FROM {self.taxonomy_schema}.data_elements
            WHERE active = TRUE
            ORDER BY element_category, element_name
        """)

        subjects = self._execute_sql(f"""
            SELECT subject_type_name, subject_description
            FROM {self.taxonomy_schema}.subject_types
            WHERE active = TRUE
        """)

        categories = self._execute_sql(f"""
            SELECT category_name, element_count
            FROM {self.taxonomy_schema}.data_categories
            WHERE active = TRUE
            ORDER BY element_count DESC
        """)

        return {
            'elements': elements,
            'subjects': [s['subject_type_name'] for s in subjects],
            'categories': categories,
            'total_elements': len(elements),
            'total_sensitive': sum(1 for e in elements if e['sensitive_flag'] == 'Yes'),
            'version': self._get_current_version()
        }

    def _create_version_record(self, version: str, element_count: int,
                               change_type: str, description: str):
        """Create version record for audit trail"""

        sql = f"""
        INSERT INTO {self.taxonomy_schema}.taxonomy_versions
        (version_number, change_type, change_description, element_count)
        VALUES (
          '{version}',
          '{change_type}',
          {self._quote(description)},
          {element_count}
        )
        """

        self._execute_sql(sql)

    def _get_current_version(self) -> str:
        """Get latest version number"""

        result = self._execute_sql(f"""
            SELECT version_number
            FROM {self.taxonomy_schema}.taxonomy_versions
            ORDER BY changed_at DESC
            LIMIT 1
        """)

        return result[0]['version_number'] if result else '1.0'

    def _generate_element_id(self, element_name: str) -> str:
        """
        Generate stable ID from element name
        'Social Security Number' → 'social_security_number'
        """
        # Remove special characters, convert to lowercase, replace spaces with underscores
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', element_name)
        return clean_name.lower().replace(' ', '_').replace('__', '_').strip('_')

    def _extract_keywords(self, element_name: str) -> List[str]:
        """
        Extract searchable keywords from element name
        'Social Security Number' → ['ssn', 'social security', 'social_sec']
        """
        keywords = [element_name.lower()]

        # Common abbreviations mapping
        abbrev_map = {
            'social security number': ['ssn', 'social_sec', 'social_security'],
            'email address': ['email', 'e_mail', 'email_addr'],
            'phone number': ['phone', 'telephone', 'mobile', 'cell'],
            'credit card': ['cc', 'credit_card', 'card_number', 'card_num'],
            'date of birth': ['dob', 'birth_date', 'birthdate'],
            'driver license': ['drivers_license', 'dl', 'license'],
            'passport': ['passport_number', 'passport_num'],
        }

        # Check if element name contains any mapped phrases
        for full_name, abbrevs in abbrev_map.items():
            if full_name in element_name.lower():
                keywords.extend(abbrevs)
                break

        return list(set(keywords))  # Remove duplicates

    def _execute_sql(self, sql: str) -> List[Dict]:
        """Execute SQL and return results"""

        try:
            if not self.warehouse_id:
                raise Exception(f"warehouse_id is not set! warehouse_id={self.warehouse_id}")

            print(f"[TaxonomyManager] Executing SQL with warehouse_id={self.warehouse_id}")

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

            if statement.status.state != StatementState.SUCCEEDED:
                error_msg = statement.status.error.message if statement.status.error else f"State: {statement.status.state}"
                raise Exception(f"Query failed: {error_msg}")

            # Extract results
            if hasattr(statement, 'result') and statement.result:
                columns = [col.name for col in statement.manifest.schema.columns] if statement.manifest else []
                data_array = statement.result.data_array if statement.result.data_array else []

                return [dict(zip(columns, row)) for row in data_array]

            return []

        except Exception as e:
            print(f"[TaxonomyManager] SQL Error: {e}")
            print(f"[TaxonomyManager] warehouse_id={self.warehouse_id}")
            raise

    def _quote(self, value: str) -> str:
        """Escape and quote string value for SQL"""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 'NULL'
        return "'" + str(value).replace("'", "''") + "'"
