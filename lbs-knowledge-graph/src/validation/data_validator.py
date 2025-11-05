#!/usr/bin/env python3
"""
Data Validator - Validate JSON structure and data integrity
Ensures all parsed data conforms to schema specifications
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import argparse


class ValidationLevel(Enum):
    """Validation severity levels"""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    level: ValidationLevel
    category: str
    message: str
    file_path: Optional[str] = None
    field: Optional[str] = None
    value: Any = None


class SchemaValidator:
    """Validates data against schema specifications"""

    # Required fields per entity type
    REQUIRED_FIELDS = {
        'page': ['id', 'url', 'title', 'type', 'hash', 'createdAt', 'updatedAt'],
        'section': ['id', 'pageId', 'type', 'order'],
        'contentItem': ['id', 'hash', 'text', 'type'],
        'topic': ['id', 'name', 'slug', 'category'],
        'category': ['id', 'name', 'slug', 'level'],
        'persona': ['id', 'name', 'type', 'description']
    }

    # Valid enum values
    PAGE_TYPES = [
        'homepage', 'program', 'faculty', 'research', 'news', 'event',
        'about', 'admissions', 'student_life', 'alumni', 'contact', 'other'
    ]

    SECTION_TYPES = [
        'hero', 'content', 'sidebar', 'navigation', 'footer', 'header',
        'callout', 'listing', 'profile', 'stats', 'testimonial', 'gallery',
        'form', 'other'
    ]

    CONTENT_TYPES = [
        'paragraph', 'heading', 'subheading', 'list', 'list_item', 'quote',
        'code', 'table', 'image', 'video', 'link', 'button', 'other'
    ]

    PERSONA_TYPES = [
        'prospective_student', 'current_student', 'alumni', 'faculty',
        'researcher', 'corporate_partner', 'media', 'recruiter', 'donor'
    ]

    def __init__(self):
        self.issues: List[ValidationIssue] = []

    def validate_required_fields(
        self, data: Dict, entity_type: str, file_path: str
    ) -> None:
        """Validate presence of required fields"""
        required = self.REQUIRED_FIELDS.get(entity_type, [])

        for field in required:
            if field not in data or data[field] is None or data[field] == '':
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="missing_field",
                    message=f"Missing required field: {field}",
                    file_path=file_path,
                    field=field
                ))

    def validate_field_types(self, data: Dict, file_path: str) -> None:
        """Validate field data types"""
        # URL validation
        if 'url' in data and data['url']:
            if not self._is_valid_url(data['url']):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="invalid_format",
                    message=f"Invalid URL format: {data['url']}",
                    file_path=file_path,
                    field='url',
                    value=data['url']
                ))
            elif not data['url'].startswith('https://london.edu'):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="invalid_domain",
                    message=f"URL not from london.edu: {data['url']}",
                    file_path=file_path,
                    field='url',
                    value=data['url']
                ))

        # Hash validation (SHA-256 should be 64 characters)
        if 'hash' in data and data['hash']:
            if not re.match(r'^[a-f0-9]{64}$', data['hash']):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="invalid_format",
                    message=f"Invalid hash format (expected SHA-256): {data['hash'][:20]}...",
                    file_path=file_path,
                    field='hash'
                ))

        # UUID validation
        if 'id' in data and data['id']:
            if not self._is_valid_uuid(data['id']):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="invalid_format",
                    message=f"ID is not a valid UUID: {data['id']}",
                    file_path=file_path,
                    field='id',
                    value=data['id']
                ))

        # Numeric validations
        if 'importance' in data:
            if not (0 <= data['importance'] <= 1):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="out_of_range",
                    message=f"importance must be 0-1, got {data['importance']}",
                    file_path=file_path,
                    field='importance',
                    value=data['importance']
                ))

        # Sentiment validation
        if 'sentiment' in data and data['sentiment']:
            sentiment = data['sentiment']
            if 'polarity' in sentiment:
                if not (-1 <= sentiment['polarity'] <= 1):
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="out_of_range",
                        message=f"sentiment.polarity must be -1 to 1, got {sentiment['polarity']}",
                        file_path=file_path,
                        field='sentiment.polarity',
                        value=sentiment['polarity']
                    ))
            if 'confidence' in sentiment:
                if not (0 <= sentiment['confidence'] <= 1):
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="out_of_range",
                        message=f"sentiment.confidence must be 0-1, got {sentiment['confidence']}",
                        file_path=file_path,
                        field='sentiment.confidence',
                        value=sentiment['confidence']
                    ))

    def validate_enum_values(self, data: Dict, file_path: str) -> None:
        """Validate enum field values"""
        if 'type' in data:
            entity_type = None

            # Determine entity type from structure
            if 'url' in data and 'sections' in data:
                entity_type = 'page'
                valid_types = self.PAGE_TYPES
            elif 'pageId' in data and 'contentItems' in data:
                entity_type = 'section'
                valid_types = self.SECTION_TYPES
            elif 'text' in data and 'hash' in data:
                entity_type = 'content'
                valid_types = self.CONTENT_TYPES
            elif 'description' in data and 'interests' in data:
                entity_type = 'persona'
                valid_types = self.PERSONA_TYPES
            else:
                return  # Can't determine type

            if data['type'] not in valid_types:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="invalid_enum",
                    message=f"Invalid {entity_type} type: {data['type']}. Must be one of: {', '.join(valid_types)}",
                    file_path=file_path,
                    field='type',
                    value=data['type']
                ))

    def validate_relationships(self, data: Dict, file_path: str) -> None:
        """Validate relationship integrity"""
        # Validate section references
        if 'sections' in data and isinstance(data['sections'], list):
            for i, section in enumerate(data['sections']):
                if not isinstance(section, dict):
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="invalid_structure",
                        message=f"Section {i} is not an object",
                        file_path=file_path,
                        field=f'sections[{i}]'
                    ))
                    continue

                # Validate section has contentItems
                if 'contentItems' not in section:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="missing_field",
                        message=f"Section {i} has no contentItems",
                        file_path=file_path,
                        field=f'sections[{i}].contentItems'
                    ))

        # Validate content items
        if 'contentItems' in data and isinstance(data['contentItems'], list):
            for i, item in enumerate(data['contentItems']):
                if not isinstance(item, dict):
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="invalid_structure",
                        message=f"ContentItem {i} is not an object",
                        file_path=file_path,
                        field=f'contentItems[{i}]'
                    ))

    def validate_data_quality(self, data: Dict, file_path: str) -> None:
        """Validate data quality metrics"""
        # Check for empty strings
        if 'title' in data and not data['title'].strip():
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="empty_field",
                message="Title is empty or whitespace only",
                file_path=file_path,
                field='title'
            ))

        if 'text' in data and not data['text'].strip():
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="empty_field",
                message="Text content is empty or whitespace only",
                file_path=file_path,
                field='text'
            ))

        # Check for unreasonably long content
        if 'text' in data and len(data['text']) > 10000:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="data_quality",
                message=f"Text content is very long ({len(data['text'])} chars)",
                file_path=file_path,
                field='text'
            ))

        # Check for missing semantic data in content items
        if 'hash' in data and 'text' in data:
            if not data.get('topics'):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    category="incomplete_semantic",
                    message="Content item has no topics assigned",
                    file_path=file_path,
                    field='topics'
                ))

            if not data.get('sentiment'):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    category="incomplete_semantic",
                    message="Content item has no sentiment analysis",
                    file_path=file_path,
                    field='sentiment'
                ))

    def _is_valid_url(self, url: str) -> bool:
        """Check if string is a valid URL"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(url))

    def _is_valid_uuid(self, uuid_str: str) -> bool:
        """Check if string is a valid UUID"""
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(uuid_str))


class DataValidator:
    """Main validator class"""

    def __init__(self, data_dir: str = "data/parsed"):
        self.data_dir = Path(data_dir)
        self.schema_validator = SchemaValidator()
        self.files_processed = 0
        self.files_failed = 0

    def validate_file(self, file_path: Path) -> None:
        """Validate a single JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            file_str = str(file_path)

            # Determine entity type
            if isinstance(data, dict):
                # Single entity
                self._validate_entity(data, file_str)
            elif isinstance(data, list):
                # Array of entities
                for i, entity in enumerate(data):
                    self._validate_entity(entity, f"{file_str}[{i}]")

            self.files_processed += 1

        except json.JSONDecodeError as e:
            self.schema_validator.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="json_parse_error",
                message=f"Failed to parse JSON: {str(e)}",
                file_path=str(file_path)
            ))
            self.files_failed += 1
        except Exception as e:
            self.schema_validator.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="validation_error",
                message=f"Validation error: {str(e)}",
                file_path=str(file_path)
            ))
            self.files_failed += 1

    def _validate_entity(self, entity: Dict, file_path: str) -> None:
        """Validate a single entity"""
        # Determine entity type
        entity_type = self._determine_entity_type(entity)

        # Run all validations
        self.schema_validator.validate_required_fields(entity, entity_type, file_path)
        self.schema_validator.validate_field_types(entity, file_path)
        self.schema_validator.validate_enum_values(entity, file_path)
        self.schema_validator.validate_relationships(entity, file_path)
        self.schema_validator.validate_data_quality(entity, file_path)

        # Recursively validate nested entities
        if 'sections' in entity:
            for section in entity['sections']:
                self._validate_entity(section, file_path)

        if 'contentItems' in entity:
            for item in entity['contentItems']:
                self._validate_entity(item, file_path)

    def _determine_entity_type(self, entity: Dict) -> str:
        """Determine entity type from structure"""
        if 'url' in entity and 'sections' in entity:
            return 'page'
        elif 'pageId' in entity and 'order' in entity:
            return 'section'
        elif 'hash' in entity and 'text' in entity:
            return 'contentItem'
        elif 'slug' in entity and 'category' in entity:
            return 'topic'
        elif 'level' in entity and 'children' in entity:
            return 'category'
        elif 'interests' in entity:
            return 'persona'
        return 'unknown'

    def validate_all(self) -> None:
        """Validate all JSON files in data directory"""
        json_files = list(self.data_dir.glob('**/*.json'))

        print(f"Validating {len(json_files)} JSON files...")

        for i, file_path in enumerate(json_files, 1):
            self.validate_file(file_path)

            if i % 100 == 0:
                print(f"  Validated {i}/{len(json_files)} files...")

        print(f"✓ Validation complete!")

    def generate_report(self) -> Dict:
        """Generate validation report"""
        issues = self.schema_validator.issues

        # Count by level
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        warnings = [i for i in issues if i.level == ValidationLevel.WARNING]
        infos = [i for i in issues if i.level == ValidationLevel.INFO]

        # Count by category
        by_category = {}
        for issue in issues:
            by_category[issue.category] = by_category.get(issue.category, 0) + 1

        return {
            'summary': {
                'files_processed': self.files_processed,
                'files_failed': self.files_failed,
                'total_issues': len(issues),
                'errors': len(errors),
                'warnings': len(warnings),
                'info': len(infos)
            },
            'by_category': by_category,
            'issues': [
                {
                    'level': issue.level.value,
                    'category': issue.category,
                    'message': issue.message,
                    'file': issue.file_path,
                    'field': issue.field
                }
                for issue in issues
            ]
        }

    def print_report(self) -> None:
        """Print validation report to console"""
        report = self.generate_report()
        summary = report['summary']

        print("\n" + "="*60)
        print("DATA VALIDATION REPORT")
        print("="*60)
        print(f"Files processed: {summary['files_processed']:,}")
        print(f"Files failed: {summary['files_failed']:,}")
        print(f"Total issues: {summary['total_issues']:,}")
        print(f"  Errors: {summary['errors']:,}")
        print(f"  Warnings: {summary['warnings']:,}")
        print(f"  Info: {summary['info']:,}")

        if report['by_category']:
            print("\nIssues by Category:")
            for category, count in sorted(
                report['by_category'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"  {category:.<40} {count:>6,}")

        # Show top issues
        errors = [i for i in report['issues'] if i['level'] == 'ERROR']
        if errors:
            print(f"\nTop Errors ({min(10, len(errors))} of {len(errors)}):")
            for i, issue in enumerate(errors[:10], 1):
                print(f"  {i}. [{issue['category']}] {issue['message']}")
                if issue['file']:
                    print(f"     File: {issue['file']}")

        print("="*60)

    def export_report(self, output_file: str = "data/validation_report.json") -> None:
        """Export validation report to JSON"""
        report = self.generate_report()

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        print(f"✓ Validation report exported to {output_path}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Validate JSON data structure and integrity'
    )
    parser.add_argument(
        '--data-dir',
        default='data/parsed',
        help='Directory containing JSON files to validate'
    )
    parser.add_argument(
        '--output',
        default='data/validation_report.json',
        help='Output file for validation report'
    )

    args = parser.parse_args()

    # Initialize validator
    validator = DataValidator(args.data_dir)

    # Run validation
    validator.validate_all()

    # Print report
    validator.print_report()

    # Export report
    validator.export_report(args.output)

    # Exit with error code if errors found
    report = validator.generate_report()
    if report['summary']['errors'] > 0:
        print("\n⚠️  Validation failed with errors!")
        exit(1)
    else:
        print("\n✓ All validation checks passed!")
        exit(0)


if __name__ == "__main__":
    main()
