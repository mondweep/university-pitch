# Data Validation Module

Comprehensive data quality validation tools for the LBS Knowledge Graph project.

## Overview

This module provides automated validation, quality metrics, and hash consolidation for parsed website data. It ensures data meets technical specifications before proceeding to knowledge graph construction.

## Scripts

### 1. `hash_consolidator.py`

Identifies duplicate content across pages using SHA-256 text hashes.

**Features:**
- Consolidates text hashes from all parsed pages
- Tracks content reuse across pages and sections
- Calculates deduplication effectiveness metrics
- Generates usage distribution statistics

**Usage:**
```bash
python hash_consolidator.py --data-dir data/parsed --output data/consolidated_hashes.json

# Find duplicates
python hash_consolidator.py --find-duplicates --min-usage 2
```

**Output:**
- `data/consolidated_hashes.json` - Comprehensive hash mapping
- Console report with deduplication statistics

### 2. `data_validator.py`

Validates JSON structure and data integrity against schema specifications.

**Features:**
- Required field validation
- Data type checking (URLs, UUIDs, hashes)
- Enum value validation
- Range validation (sentiment, importance scores)
- Relationship integrity checks
- Data quality assessments

**Usage:**
```bash
python data_validator.py --data-dir data/parsed --output data/validation_report.json
```

**Output:**
- `data/validation_report.json` - Detailed validation report
- Console report with issue breakdown
- Exit code 0 (success) or 1 (errors found)

### 3. `quality_metrics.py`

Calculates comprehensive data quality metrics.

**Features:**
- Completeness metrics (pages, sections, content)
- Semantic enrichment coverage (sentiment, topics, audiences)
- Deduplication analysis
- Error rate tracking
- Relationship metrics (links, broken links)
- Requirements compliance checking

**Usage:**
```bash
python quality_metrics.py --data-dir data/parsed --output data/quality_metrics.json
```

**Output:**
- `data/quality_metrics.json` - Quality metrics report
- Console report with percentage scores
- Exit code 0 (passed) or 1 (requirements not met)

### 4. `run_validation.py` ⭐ **Master Script**

Orchestrates all validation processes in a single pipeline.

**Features:**
- Runs all validation steps sequentially
- Generates comprehensive results
- Creates markdown report for documentation
- Provides unified status reporting

**Usage:**
```bash
# Run complete validation pipeline
python run_validation.py --data-dir data/parsed --output-dir data/validation

# Outputs:
# - data/validation/consolidated_hashes.json
# - data/validation/validation_report.json
# - data/validation/quality_metrics.json
# - data/validation/validation_results.json
# - lbs-knowledge-graph/docs/DATA_QUALITY_REPORT.md
```

## Quality Requirements

Based on `plans/03_TECHNICAL_SPECIFICATIONS.md`:

### Minimum Standards
- **Data Completeness:** 95%+ (page titles, content text, hashes)
- **Deduplication Rate:** 80%+ duplicate detection
- **Schema Compliance:** 100% valid JSON structure
- **Error Rate:** < 5% validation errors

### Validation Levels
- **ERROR** - Critical issues, must be fixed
- **WARNING** - Non-critical issues, should be reviewed
- **INFO** - Informational, for optimization

## Integration with Phase 1

This validation module is part of Phase 1 (Foundation) in the project timeline:

```
Phase 1: Foundation (Weeks 1-2)
├── Crawling & Parsing
├── Hash System Implementation
└── Data Validation ← This module
    ├── Hash consolidation
    ├── Schema validation
    └── Quality metrics
```

## Output Files

### 1. Consolidated Hashes
```json
{
  "version": "1.0",
  "statistics": {
    "total_unique_hashes": 1250,
    "total_occurrences": 3500,
    "deduplication_metrics": {...}
  },
  "hashes": {
    "abc123...": {
      "text": "Content text...",
      "usage_count": 5,
      "pages": ["page-1", "page-2"]
    }
  }
}
```

### 2. Validation Report
```json
{
  "summary": {
    "files_processed": 500,
    "total_issues": 42,
    "errors": 0,
    "warnings": 35
  },
  "issues": [...]
}
```

### 3. Quality Metrics
```json
{
  "summary": {
    "passes_requirements": true
  },
  "completeness": {
    "pages": {"title": 98.5},
    "content": {"text": 96.2}
  },
  "semantic_enrichment": {
    "sentiment": 45.3,
    "topics": 62.1
  }
}
```

## Troubleshooting

### Common Issues

**Issue:** Hash validation errors
```
Solution: Ensure text is properly hashed with SHA-256 (64 hex chars)
Check: hash_consolidator.py output for format issues
```

**Issue:** Low deduplication rate
```
Solution: Review content extraction logic in parser
Expected: 80%+ for navigation/headers/footers
```

**Issue:** Schema validation failures
```
Solution: Review data against plans/04_DATA_MODEL_SCHEMA.md
Check: Required fields, enum values, data types
```

## Development

### Adding New Validations

1. Update `SchemaValidator` class in `data_validator.py`
2. Add new validation method
3. Call from `_validate_entity()`
4. Update tests

### Adding New Metrics

1. Update `QualityMetrics` dataclass in `quality_metrics.py`
2. Add calculation in `analyze_*` methods
3. Update `calculate_percentages()` if needed
4. Add to report generation

## Testing

```bash
# Test with sample data
python run_validation.py --data-dir tests/fixtures/sample_data

# Verify outputs
ls -lh data/validation/
```

## Next Steps

After successful validation:
1. Review `lbs-knowledge-graph/docs/DATA_QUALITY_REPORT.md`
2. Address any critical issues
3. Proceed to Phase 2: Knowledge Graph Construction

## Dependencies

- Python 3.8+
- Standard library only (no external dependencies)
- Works with JSON files from parser output

## Author

Data Quality Specialist Agent
Phase 1, LBS Knowledge Graph Project
