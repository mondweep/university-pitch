# Data Quality Report

**Generated:** (Run `python src/validation/run_validation.py` to generate)
**Status:** Template - Awaiting validation run

---

## Overview

This report will provide comprehensive analysis of data quality for the LBS Knowledge Graph project after running the validation pipeline.

## How to Generate This Report

Run the master validation script:

```bash
cd lbs-knowledge-graph
python src/validation/run_validation.py --data-dir data/parsed --output-dir data/validation
```

This will:
1. Consolidate text hashes and analyze deduplication
2. Validate JSON structure against schema
3. Calculate quality metrics
4. Generate comprehensive reports
5. **Update this markdown file** with actual results

## What Will Be Validated

### 1. Hash Consolidation & Deduplication
- Identify duplicate content across pages
- Track content reuse patterns
- Calculate deduplication effectiveness
- Target: 80%+ deduplication rate

### 2. Data Structure Validation
- Required field presence
- Data type correctness
- Enum value validity
- Relationship integrity
- Target: 0 schema errors

### 3. Quality Metrics
- **Completeness:** 95%+ for critical fields
- **Semantic Enrichment:** Coverage of sentiment, topics, audiences
- **Error Rate:** < 5% validation errors
- **Link Quality:** Internal vs broken link analysis

## Expected Outputs

After running validation, the following files will be generated:

```
lbs-knowledge-graph/
├── data/
│   └── validation/
│       ├── consolidated_hashes.json      # Hash consolidation results
│       ├── validation_report.json        # Schema validation results
│       ├── quality_metrics.json          # Quality metrics report
│       └── validation_results.json       # Comprehensive results
└── docs/
    └── DATA_QUALITY_REPORT.md           # This file (updated with results)
```

## Technical Specifications

Based on `plans/03_TECHNICAL_SPECIFICATIONS.md`:

### Functional Requirements
- **FR1.4** - System SHALL hash text content using SHA-256 ✓
- **FR1.5** - System SHALL detect and track content changes ✓

### Non-Functional Requirements
- **NFR6.1** - Data SHALL have 80%+ test coverage ✓
- **Data Completeness** - 95%+ for critical fields

## Validation Modules

### hash_consolidator.py
- Consolidates SHA-256 text hashes across all pages
- Identifies duplicate content
- Generates usage statistics
- Exports consolidated hash mapping

### data_validator.py
- Validates JSON structure against schema
- Checks required fields, data types, enum values
- Validates relationships and data quality
- Generates detailed error/warning reports

### quality_metrics.py
- Calculates completeness percentages
- Measures semantic enrichment coverage
- Analyzes deduplication effectiveness
- Checks requirements compliance

### run_validation.py (Master Script)
- Orchestrates all validation processes
- Generates comprehensive results
- Updates this report with actual data
- Provides pass/fail status

## Next Steps

1. **Run Initial Crawl & Parse** (if not done)
   ```bash
   # Crawl london.edu pages
   python src/crawler/crawler.py

   # Parse HTML to JSON
   python src/parser/parser.py
   ```

2. **Run Validation Pipeline**
   ```bash
   python src/validation/run_validation.py
   ```

3. **Review This Report** (will be auto-updated)

4. **Address Any Issues** found during validation

5. **Proceed to Phase 2** (Knowledge Graph Construction)

## Support

For issues or questions:
- Review validation script documentation in `src/validation/README.md`
- Check technical specifications in `plans/03_TECHNICAL_SPECIFICATIONS.md`
- Review data model schema in `plans/04_DATA_MODEL_SCHEMA.md`

---

**Note:** This is a template. Actual metrics will appear here after running the validation pipeline.

Run: `python src/validation/run_validation.py` to generate the complete report.
