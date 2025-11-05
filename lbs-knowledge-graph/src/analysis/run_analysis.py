#!/usr/bin/env python3
"""
Analysis Runner for LBS Knowledge Graph Project.

Orchestrates pattern analysis and extraction validation:
1. Run pattern analysis on parsed content
2. Create/load ground truth dataset
3. Validate extraction accuracy
4. Generate comprehensive reports
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from analysis.pattern_analyzer import PatternAnalyzer
from analysis.extraction_validator import ExtractionValidator
from analysis.ground_truth import GroundTruthBuilder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_pattern_analysis(parsed_dir: Path, output_dir: Path) -> Path:
    """
    Run comprehensive pattern analysis.

    Args:
        parsed_dir: Directory with parsed content
        output_dir: Directory for output files

    Returns:
        Path to pattern report
    """
    logger.info("="*60)
    logger.info("STEP 1: Pattern Analysis")
    logger.info("="*60)

    analyzer = PatternAnalyzer(parsed_dir)
    report = analyzer.generate_report()

    # Save report
    output_file = output_dir / f"pattern_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report.to_json(output_file)

    # Print summary
    print(f"\n📊 Pattern Analysis Summary:")
    print(f"   Total pages analyzed: {report.total_pages}")
    print(f"   Page types found: {len(report.page_type_patterns.get('page_type_distribution', {}))}")
    print(f"   Section types found: {len(report.section_type_patterns.get('section_types', {}))}")
    print(f"   Unique text blocks: {report.text_reuse_statistics.get('total_unique_texts', 0)}")
    print(f"   Text reuse ratio: {report.text_reuse_statistics.get('reuse_ratio', 0):.2f}x")
    print(f"\n   Report saved to: {output_file}")

    return output_file


def create_ground_truth(
    parsed_dir: Path,
    output_dir: Path,
    mode: str = 'automated',
    num_samples: int = 20
) -> Path:
    """
    Create ground truth dataset.

    Args:
        parsed_dir: Directory with parsed content
        output_dir: Directory for output files
        mode: 'automated' or 'interactive'
        num_samples: Number of pages to sample

    Returns:
        Path to ground truth file (validator format)
    """
    logger.info("="*60)
    logger.info("STEP 2: Ground Truth Creation")
    logger.info("="*60)

    ground_truth_dir = output_dir / 'ground_truth'
    builder = GroundTruthBuilder(parsed_dir, ground_truth_dir)

    # Sample pages
    samples = builder.sample_pages(num_samples, strategy='diverse')

    # Create dataset based on mode
    if mode == 'interactive':
        logger.info(f"Starting interactive labeling for {len(samples)} pages...")
        dataset = builder.create_interactive_labeling_session(samples)
    else:
        logger.info(f"Creating automated labels for {len(samples)} pages...")
        dataset = builder.create_automated_ground_truth(samples)

    # Save dataset
    dataset.to_json(ground_truth_dir / f"{dataset.name}.json")

    # Export for validator
    validator_file = builder.export_for_validation(dataset)

    print(f"\n📋 Ground Truth Summary:")
    print(f"   Mode: {mode}")
    print(f"   Labeled pages: {len(dataset.entries)}")
    print(f"   Dataset: {ground_truth_dir / dataset.name}.json")
    print(f"   Validator format: {validator_file}")

    return validator_file


def run_validation(
    parsed_dir: Path,
    ground_truth_file: Path,
    output_dir: Path
) -> Path:
    """
    Run extraction validation.

    Args:
        parsed_dir: Directory with parsed content
        ground_truth_file: Ground truth dataset (validator format)
        output_dir: Directory for output files

    Returns:
        Path to validation report
    """
    logger.info("="*60)
    logger.info("STEP 3: Extraction Validation")
    logger.info("="*60)

    # Load parsed pages as mock extracted data
    pages = []
    for page_dir in parsed_dir.iterdir():
        if page_dir.is_dir():
            metadata_file = page_dir / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)

                pages.append({
                    'page_name': page_dir.name,
                    'type': _infer_type(page_dir.name),
                    'title': metadata.get('title', ''),
                    'url': metadata.get('canonical_url', '')
                })

    # Create validator
    validator = ExtractionValidator(ground_truth_file)

    # Run validation
    report = validator.validate_all(
        pages=pages,
        sections=[],  # TODO: Add when section extractor is ready
        content_items=[]  # TODO: Add when content extractor is ready
    )

    # Save report
    output_file = output_dir / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report.to_json(output_file)

    # Print summary
    print(f"\n✅ Validation Summary:")
    print(f"   Pages validated: {report.overall_metrics['total_pages']}")
    print(f"   Page classification accuracy: {report.page_type_metrics['overall'].accuracy:.2%}")
    print(f"   Precision: {report.page_type_metrics['overall'].precision:.2%}")
    print(f"   Recall: {report.page_type_metrics['overall'].recall:.2%}")
    print(f"   F1 Score: {report.page_type_metrics['overall'].f1_score:.2%}")
    print(f"   Errors found: {len(report.errors)}")
    print(f"\n   Report saved to: {output_file}")

    return output_file


def generate_markdown_report(
    pattern_report_file: Path,
    validation_report_file: Path,
    output_dir: Path
) -> Path:
    """
    Generate comprehensive markdown report.

    Args:
        pattern_report_file: Pattern analysis report
        validation_report_file: Validation report
        output_dir: Output directory

    Returns:
        Path to markdown report
    """
    logger.info("="*60)
    logger.info("STEP 4: Generate Comprehensive Report")
    logger.info("="*60)

    # Load reports
    with open(pattern_report_file) as f:
        pattern_data = json.load(f)

    with open(validation_report_file) as f:
        validation_data = json.load(f)

    # Generate markdown
    md_content = f"""# LBS Knowledge Graph - Pattern Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary

This report analyzes content patterns from the London Business School website crawl and validates
the accuracy of domain model extractors.

### Key Metrics

- **Total Pages Analyzed:** {pattern_data['total_pages']}
- **Page Classification Accuracy:** {validation_data['overall_metrics']['avg_accuracy']:.1%}
- **Section Detection Accuracy:** {validation_data['section_type_metrics']['overall']['accuracy']:.1%}
- **Content Extraction Accuracy:** {validation_data['content_type_metrics']['overall']['accuracy']:.1%}
- **Overall F1 Score:** {validation_data['overall_metrics']['avg_f1']:.1%}

---

## 1. Pattern Analysis Results

### 1.1 Page Type Distribution

"""

    # Add page type distribution
    page_types = pattern_data['page_type_patterns']['page_type_distribution']
    md_content += "| Page Type | Count | Percentage |\n"
    md_content += "|-----------|-------|------------|\n"

    total = pattern_data['total_pages']
    for page_type, count in sorted(page_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total * 100) if total > 0 else 0
        md_content += f"| {page_type} | {count} | {percentage:.1f}% |\n"

    md_content += f"""

### 1.2 Section Type Patterns

Top section types identified:

"""

    # Add section types
    section_types = pattern_data['section_type_patterns']['section_types']
    for section_type, count in list(section_types.items())[:10]:
        md_content += f"- **{section_type}**: {count} occurrences\n"

    md_content += f"""

### 1.3 Content Reuse Statistics

- **Unique text blocks:** {pattern_data['text_reuse_statistics']['total_unique_texts']}
- **Total text instances:** {pattern_data['text_reuse_statistics']['total_text_instances']}
- **Reuse ratio:** {pattern_data['text_reuse_statistics']['reuse_ratio']:.2f}x

**Reuse Distribution:**

"""

    reuse_dist = pattern_data['text_reuse_statistics']['reuse_distribution']
    for category, count in reuse_dist.items():
        md_content += f"- {category.replace('_', ' ').title()}: {count}\n"

    md_content += f"""

### 1.4 Most Reused Content

Top 5 most reused text blocks:

"""

    for i, item in enumerate(pattern_data['text_reuse_statistics']['most_reused'][:5], 1):
        md_content += f"{i}. **{item['text'][:60]}...** ({item['usage_count']} uses)\n"

    md_content += f"""

---

## 2. Extraction Validation Results

### 2.1 Page Classification

**Metrics:**

- **Accuracy:** {validation_data['page_type_metrics']['overall']['accuracy']:.1%}
- **Precision:** {validation_data['page_type_metrics']['overall']['precision']:.1%}
- **Recall:** {validation_data['page_type_metrics']['overall']['recall']:.1%}
- **F1 Score:** {validation_data['page_type_metrics']['overall']['f1_score']:.1%}

**Classification Results:**

- True Positives: {validation_data['page_type_metrics']['overall']['true_positives']}
- False Positives: {validation_data['page_type_metrics']['overall']['false_positives']}
- False Negatives: {validation_data['page_type_metrics']['overall']['false_negatives']}

### 2.2 Errors and Misclassifications

Total errors found: {len(validation_data['errors'])}

"""

    if validation_data['errors']:
        md_content += "**Sample Errors:**\n\n"
        for i, error in enumerate(validation_data['errors'][:5], 1):
            md_content += f"{i}. **{error.get('entity_id', 'N/A')}**\n"
            md_content += f"   - Expected: {error.get('expected', 'N/A')}\n"
            md_content += f"   - Extracted: {error.get('extracted', 'N/A')}\n"
            md_content += f"   - URL: {error.get('url', 'N/A')}\n\n"

    md_content += f"""

---

## 3. Recommendations

### 3.1 High Priority Improvements

Based on validation results, the following areas need attention:

"""

    # Add recommendations based on accuracy
    page_accuracy = validation_data['page_type_metrics']['overall']['accuracy']

    if page_accuracy < 0.90:
        md_content += "- **Improve page type classification** (current accuracy: {:.1%})\n".format(page_accuracy)
        md_content += "  - Review URL pattern matching rules\n"
        md_content += "  - Add content-based classification fallbacks\n"
        md_content += "  - Expand training data for edge cases\n\n"

    md_content += """
### 3.2 Next Steps for Phase 2

1. **Refine Extractors:**
   - Implement fixes for identified errors
   - Add additional pattern matching rules
   - Improve classification confidence

2. **Expand Ground Truth:**
   - Manually label 20-30 additional pages
   - Focus on misclassified pages
   - Create section and content ground truth

3. **Validation:**
   - Re-run validation after improvements
   - Target 90%+ accuracy for all entity types
   - Document final accuracy metrics

---

## 4. Appendices

### 4.1 Analysis Files

- **Pattern Report:** `{pattern_report_file.name}`
- **Validation Report:** `{validation_report_file.name}`

### 4.2 Methodology

**Pattern Analysis:**
- Analyzed {pattern_data['total_pages']} crawled pages
- Identified page types, section types, and content patterns
- Calculated text reuse statistics

**Validation:**
- Compared extracted classifications against ground truth
- Calculated precision, recall, and F1 scores
- Identified misclassifications and errors

---

**Report End**
"""

    # Save markdown
    output_file = output_dir / f"PATTERN_ANALYSIS_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_file, 'w') as f:
        f.write(md_content)

    print(f"\n📄 Comprehensive markdown report generated:")
    print(f"   {output_file}")

    return output_file


def _infer_type(page_name: str) -> str:
    """Helper to infer page type from name."""
    page_name_lower = page_name.lower()
    if 'homepage' in page_name_lower:
        return 'homepage'
    elif 'programme' in page_name_lower or 'program' in page_name_lower:
        return 'programme'
    elif 'faculty' in page_name_lower:
        return 'faculty'
    elif 'news' in page_name_lower:
        return 'news'
    elif 'event' in page_name_lower:
        return 'event'
    elif 'alumni' in page_name_lower:
        return 'alumni'
    elif 'about' in page_name_lower:
        return 'about'
    elif 'contact' in page_name_lower:
        return 'contact'
    else:
        return 'other'


def main():
    """Main analysis runner."""
    if len(sys.argv) < 2:
        print("Usage: python run_analysis.py <parsed_dir> [mode] [num_samples]")
        print("Modes: automated (default), interactive")
        sys.exit(1)

    parsed_dir = Path(sys.argv[1])
    mode = sys.argv[2] if len(sys.argv) > 2 else 'automated'
    num_samples = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    if not parsed_dir.exists():
        logger.error(f"Parsed directory not found: {parsed_dir}")
        sys.exit(1)

    # Create output directory
    output_dir = parsed_dir.parent / 'analysis'
    output_dir.mkdir(exist_ok=True)

    print("\n" + "="*60)
    print("LBS Knowledge Graph - Pattern Analysis & Validation")
    print("="*60 + "\n")

    try:
        # Step 1: Pattern Analysis
        pattern_report = run_pattern_analysis(parsed_dir, output_dir)

        # Step 2: Ground Truth Creation
        ground_truth_file = create_ground_truth(parsed_dir, output_dir, mode, num_samples)

        # Step 3: Validation
        validation_report = run_validation(parsed_dir, ground_truth_file, output_dir)

        # Step 4: Comprehensive Report
        markdown_report = generate_markdown_report(pattern_report, validation_report, output_dir)

        print("\n" + "="*60)
        print("✨ Analysis Complete!")
        print("="*60)
        print(f"\nAll reports saved to: {output_dir}")
        print(f"\n📊 Pattern Report: {pattern_report.name}")
        print(f"📋 Ground Truth: {ground_truth_file.name}")
        print(f"✅ Validation Report: {validation_report.name}")
        print(f"📄 Markdown Report: {markdown_report.name}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
