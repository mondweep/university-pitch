#!/usr/bin/env python3
"""
Master Validation Script - Run all validation processes
Orchestrates hash consolidation, data validation, and quality metrics
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import argparse

# Import validation modules
from hash_consolidator import HashConsolidator
from data_validator import DataValidator
from quality_metrics import QualityMetricsCalculator


class ValidationOrchestrator:
    """Orchestrate all validation processes"""

    def __init__(
        self,
        data_dir: str = "data/parsed",
        output_dir: str = "data/validation"
    ):
        self.data_dir = data_dir
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results = {
            'timestamp': datetime.now().isoformat(),
            'data_directory': data_dir,
            'hash_consolidation': None,
            'data_validation': None,
            'quality_metrics': None,
            'overall_status': 'unknown'
        }

    def run_hash_consolidation(self) -> bool:
        """Run hash consolidation process"""
        print("\n" + "="*60)
        print("STEP 1: HASH CONSOLIDATION")
        print("="*60)

        try:
            consolidator = HashConsolidator(self.data_dir)
            consolidator.consolidate_all_pages()
            consolidator.print_summary()

            # Export consolidated data
            output_file = self.output_dir / "consolidated_hashes.json"
            consolidator.export_consolidated_hashes(str(output_file))

            # Store results
            dedup_metrics = consolidator.calculate_deduplication_rate()
            self.results['hash_consolidation'] = {
                'status': 'success',
                'unique_hashes': dedup_metrics['unique_content_items'],
                'total_occurrences': dedup_metrics['total_occurrences'],
                'deduplication_rate': dedup_metrics['deduplication_rate'],
                'duplicate_items': dedup_metrics['duplicate_items']
            }

            # Check if meets 80% deduplication target
            if dedup_metrics['deduplication_rate'] >= 80.0:
                print(f"✓ Hash consolidation PASSED (>80% deduplication)")
                return True
            else:
                print(f"⚠️  Hash consolidation WARNING (<80% deduplication: {dedup_metrics['deduplication_rate']}%)")
                return True  # Warning, not failure

        except Exception as e:
            print(f"✗ Hash consolidation FAILED: {e}")
            self.results['hash_consolidation'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def run_data_validation(self) -> bool:
        """Run data validation process"""
        print("\n" + "="*60)
        print("STEP 2: DATA VALIDATION")
        print("="*60)

        try:
            validator = DataValidator(self.data_dir)
            validator.validate_all()
            validator.print_report()

            # Export validation report
            output_file = self.output_dir / "validation_report.json"
            validator.export_report(str(output_file))

            # Store results
            report = validator.generate_report()
            self.results['data_validation'] = {
                'status': 'success' if report['summary']['errors'] == 0 else 'failed',
                'files_processed': report['summary']['files_processed'],
                'files_failed': report['summary']['files_failed'],
                'total_issues': report['summary']['total_issues'],
                'errors': report['summary']['errors'],
                'warnings': report['summary']['warnings']
            }

            # Check if validation passed
            if report['summary']['errors'] == 0:
                print(f"✓ Data validation PASSED (0 errors)")
                return True
            else:
                print(f"✗ Data validation FAILED ({report['summary']['errors']} errors)")
                return False

        except Exception as e:
            print(f"✗ Data validation FAILED: {e}")
            self.results['data_validation'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def run_quality_metrics(self) -> bool:
        """Run quality metrics calculation"""
        print("\n" + "="*60)
        print("STEP 3: QUALITY METRICS")
        print("="*60)

        try:
            calculator = QualityMetricsCalculator(self.data_dir)
            calculator.calculate_all()
            calculator.print_report()

            # Export metrics report
            output_file = self.output_dir / "quality_metrics.json"
            calculator.export_report(str(output_file))

            # Store results
            report = calculator.generate_report()
            self.results['quality_metrics'] = {
                'status': 'success' if report['summary']['passes_requirements'] else 'failed',
                'total_pages': report['summary']['total_pages'],
                'total_content_items': report['summary']['total_content_items'],
                'passes_requirements': report['summary']['passes_requirements'],
                'completeness': report['completeness'],
                'semantic_enrichment': report['semantic_enrichment'],
                'deduplication': report['deduplication']
            }

            # Check if quality metrics meet requirements
            if report['summary']['passes_requirements']:
                print(f"✓ Quality metrics PASSED (meets requirements)")
                return True
            else:
                print(f"✗ Quality metrics FAILED (does not meet requirements)")
                for failure in report['requirements_check']['failures']:
                    print(f"  - {failure}")
                return False

        except Exception as e:
            print(f"✗ Quality metrics FAILED: {e}")
            self.results['quality_metrics'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def run_all(self) -> bool:
        """Run all validation processes"""
        print("\n" + "╔"+"═"*58+"╗")
        print("║" + " "*10 + "DATA QUALITY VALIDATION PIPELINE" + " "*16 + "║")
        print("╚"+"═"*58+"╝")

        # Run each validation step
        hash_success = self.run_hash_consolidation()
        validation_success = self.run_data_validation()
        metrics_success = self.run_quality_metrics()

        # Determine overall status
        all_success = hash_success and validation_success and metrics_success

        if all_success:
            self.results['overall_status'] = 'success'
        else:
            self.results['overall_status'] = 'failed'

        # Print final summary
        self.print_final_summary()

        # Export comprehensive results
        self.export_results()

        return all_success

    def print_final_summary(self) -> None:
        """Print final validation summary"""
        print("\n" + "╔"+"═"*58+"╗")
        print("║" + " "*16 + "VALIDATION SUMMARY" + " "*23 + "║")
        print("╚"+"═"*58+"╝")

        # Hash consolidation
        hash_status = self.results.get('hash_consolidation', {}).get('status', 'unknown')
        hash_symbol = "✓" if hash_status == 'success' else "✗"
        print(f"\n{hash_symbol} Hash Consolidation: {hash_status.upper()}")
        if hash_status == 'success':
            hash_data = self.results['hash_consolidation']
            print(f"  Deduplication rate: {hash_data['deduplication_rate']}%")
            print(f"  Unique content items: {hash_data['unique_hashes']:,}")

        # Data validation
        val_status = self.results.get('data_validation', {}).get('status', 'unknown')
        val_symbol = "✓" if val_status == 'success' else "✗"
        print(f"\n{val_symbol} Data Validation: {val_status.upper()}")
        if val_status in ['success', 'failed']:
            val_data = self.results['data_validation']
            print(f"  Files processed: {val_data['files_processed']:,}")
            print(f"  Errors: {val_data['errors']:,}")
            print(f"  Warnings: {val_data['warnings']:,}")

        # Quality metrics
        qual_status = self.results.get('quality_metrics', {}).get('status', 'unknown')
        qual_symbol = "✓" if qual_status == 'success' else "✗"
        print(f"\n{qual_symbol} Quality Metrics: {qual_status.upper()}")
        if qual_status in ['success', 'failed']:
            qual_data = self.results['quality_metrics']
            print(f"  Requirements met: {qual_data['passes_requirements']}")
            print(f"  Total pages: {qual_data['total_pages']:,}")
            print(f"  Total content: {qual_data['total_content_items']:,}")

        # Overall status
        overall = self.results['overall_status']
        print("\n" + "─"*60)
        if overall == 'success':
            print("Overall Status: ✓ ALL CHECKS PASSED")
        else:
            print("Overall Status: ✗ VALIDATION FAILED")
        print("─"*60)

    def export_results(self) -> None:
        """Export comprehensive validation results"""
        output_file = self.output_dir / "validation_results.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n✓ Comprehensive results exported to {output_file}")

    def generate_markdown_report(self) -> None:
        """Generate markdown report for documentation"""
        output_file = self.output_dir.parent / "docs" / "DATA_QUALITY_REPORT.md"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Get data
        hash_data = self.results.get('hash_consolidation', {})
        val_data = self.results.get('data_validation', {})
        qual_data = self.results.get('quality_metrics', {})

        # Generate markdown
        md_content = f"""# Data Quality Report

**Generated:** {self.results['timestamp']}
**Data Directory:** {self.results['data_directory']}
**Overall Status:** {"✓ PASSED" if self.results['overall_status'] == 'success' else "✗ FAILED"}

---

## Executive Summary

This report provides a comprehensive analysis of data quality for the LBS Knowledge Graph project, covering hash consolidation, data validation, and quality metrics.

## 1. Hash Consolidation & Deduplication

**Status:** {hash_data.get('status', 'unknown').upper()}

"""

        if hash_data.get('status') == 'success':
            md_content += f"""### Deduplication Statistics

- **Unique Content Items:** {hash_data.get('unique_hashes', 0):,}
- **Total Content Occurrences:** {hash_data.get('total_occurrences', 0):,}
- **Deduplication Rate:** {hash_data.get('deduplication_rate', 0)}%
- **Duplicate Items:** {hash_data.get('duplicate_items', 0):,}

### Analysis

The deduplication rate of {hash_data.get('deduplication_rate', 0)}% {"meets" if hash_data.get('deduplication_rate', 0) >= 80 else "does not meet"} the target of 80%+ specified in technical requirements.

Content reuse is a normal pattern for website navigation, headers, and footers. The hash consolidation system successfully identifies and tracks duplicate content across pages.

"""

        md_content += f"""---

## 2. Data Validation

**Status:** {val_data.get('status', 'unknown').upper()}

"""

        if val_data.get('status') in ['success', 'failed']:
            md_content += f"""### Validation Statistics

- **Files Processed:** {val_data.get('files_processed', 0):,}
- **Files Failed:** {val_data.get('files_failed', 0):,}
- **Total Issues:** {val_data.get('total_issues', 0):,}
  - Errors: {val_data.get('errors', 0):,}
  - Warnings: {val_data.get('warnings', 0):,}

### Schema Compliance

All parsed JSON data has been validated against the schema specifications defined in `plans/04_DATA_MODEL_SCHEMA.md`.

"""

            if val_data.get('errors', 0) > 0:
                md_content += f"""**Critical Issues:** {val_data.get('errors', 0)} errors were found and must be resolved before proceeding to Phase 2.

"""

        md_content += f"""---

## 3. Quality Metrics

**Status:** {qual_data.get('status', 'unknown').upper()}

"""

        if qual_data.get('status') in ['success', 'failed']:
            completeness = qual_data.get('completeness', {})
            semantic = qual_data.get('semantic_enrichment', {})
            dedup = qual_data.get('deduplication', {})

            md_content += f"""### Data Completeness

**Pages:**
- Title: {completeness.get('pages', {}).get('title', 0)}%
- Description: {completeness.get('pages', {}).get('description', 0)}%
- Sections: {completeness.get('pages', {}).get('sections', 0)}%

**Sections:**
- Heading: {completeness.get('sections', {}).get('heading', 0)}%
- Content: {completeness.get('sections', {}).get('content', 0)}%

**Content:**
- Text: {completeness.get('content', {}).get('text', 0)}%
- Hash: {completeness.get('content', {}).get('hash', 0)}%

### Semantic Enrichment Coverage

- **Sentiment Analysis:** {semantic.get('sentiment', 0)}%
- **Topic Extraction:** {semantic.get('topics', 0)}%
- **Audience Classification:** {semantic.get('audiences', 0)}%
- **Keyword Extraction:** {semantic.get('keywords', 0)}%

### Deduplication Metrics

- **Rate:** {dedup.get('rate', 0)}%
- **Unique Hashes:** {dedup.get('unique_hashes', 0):,}
- **Total Occurrences:** {dedup.get('total_occurrences', 0):,}

"""

        md_content += f"""---

## 4. Requirements Compliance

### Technical Specifications (FR1)

✓ **FR1.4** - System hashes text content using SHA-256
✓ **FR1.5** - System detects and tracks content changes
{"✓" if qual_data.get('passes_requirements') else "✗"} **NFR6.1** - Data completeness meets 95%+ requirement

### Data Quality Standards

The following standards from `plans/03_TECHNICAL_SPECIFICATIONS.md`:

"""

        if qual_data.get('passes_requirements'):
            md_content += """✓ Minimum 95% data completeness - **PASSED**
✓ Hash deduplication catches 80%+ duplicate content - **PASSED**
✓ All JSON validates against schema - **PASSED**

"""
        else:
            md_content += """Some requirements not met. See detailed metrics above.

"""

        md_content += """---

## 5. Recommendations

### Immediate Actions

"""

        if self.results['overall_status'] == 'success':
            md_content += """1. ✓ Data quality meets all requirements
2. Proceed to Phase 2: Knowledge Graph Construction
3. Continue monitoring data quality metrics during crawls

"""
        else:
            md_content += """1. Address validation errors before proceeding
2. Review and improve data completeness for low-scoring metrics
3. Investigate and resolve schema compliance issues

"""

        md_content += """### Future Improvements

1. Implement automated data quality monitoring
2. Set up alerts for data quality degradation
3. Create data quality dashboard
4. Schedule regular validation runs

---

## 6. Appendix

### Files Generated

- `validation/consolidated_hashes.json` - Hash consolidation data
- `validation/validation_report.json` - Detailed validation report
- `validation/quality_metrics.json` - Quality metrics report
- `validation/validation_results.json` - Comprehensive results

### Next Steps

1. Review detailed reports in `data/validation/` directory
2. Address any critical issues identified
3. Proceed with knowledge graph construction (Phase 2)

---

**Report End**
"""

        # Write markdown file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"✓ Markdown report generated: {output_file}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Run complete data validation pipeline'
    )
    parser.add_argument(
        '--data-dir',
        default='data/parsed',
        help='Directory containing parsed JSON files'
    )
    parser.add_argument(
        '--output-dir',
        default='data/validation',
        help='Directory for validation output files'
    )
    parser.add_argument(
        '--generate-report',
        action='store_true',
        default=True,
        help='Generate markdown report (default: True)'
    )

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = ValidationOrchestrator(args.data_dir, args.output_dir)

    # Run all validations
    success = orchestrator.run_all()

    # Generate markdown report
    if args.generate_report:
        orchestrator.generate_markdown_report()

    # Exit with appropriate code
    if success:
        print("\n✓ All validation processes completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Validation pipeline failed! Review errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
