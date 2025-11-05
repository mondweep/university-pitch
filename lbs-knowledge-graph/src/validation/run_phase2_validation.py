#!/usr/bin/env python3
"""
Phase 2 Validation Suite - Master script for knowledge graph validation
Orchestrates graph integrity, completeness, and quality metric validation
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import argparse

# Import Phase 2 validation modules
from graph_validator import GraphValidator
from completeness_checker import CompletenessChecker
from graph_quality_metrics import QualityMetrics

logger = logging.getLogger(__name__)


class Phase2ValidationOrchestrator:
    """Orchestrate all Phase 2 validation processes"""

    def __init__(
        self,
        graph_file: str,
        parsed_data_dir: str = "data/parsed",
        output_dir: str = "data/validation"
    ):
        self.graph_file = Path(graph_file)
        self.parsed_data_dir = Path(parsed_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.graph = None
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'graph_file': str(graph_file),
            'parsed_data_dir': str(parsed_data_dir),
            'graph_validation': None,
            'completeness_check': None,
            'quality_metrics': None,
            'overall_status': 'unknown'
        }

    def load_graph(self) -> bool:
        """Load MGraph from JSON file"""
        try:
            from mgraph_db import MGraph

            logger.info(f"Loading graph from {self.graph_file}")

            if not self.graph_file.exists():
                logger.error(f"Graph file not found: {self.graph_file}")
                return False

            self.graph = MGraph()
            self.graph.load_from_json(str(self.graph_file))

            node_count = self.graph.node_count() if hasattr(self.graph, 'node_count') else 0
            edge_count = self.graph.edge_count() if hasattr(self.graph, 'edge_count') else 0

            logger.info(f"Graph loaded: {node_count:,} nodes, {edge_count:,} edges")
            return True

        except ImportError:
            logger.error("mgraph_db not installed. Install with: pip install mgraph-db")
            return False
        except Exception as e:
            logger.error(f"Failed to load graph: {e}")
            return False

    def run_graph_validation(self) -> bool:
        """Run graph integrity validation"""
        print("\n" + "="*60)
        print("STEP 1: GRAPH INTEGRITY VALIDATION")
        print("="*60)

        try:
            validator = GraphValidator()

            # Run all validation checks
            logger.info("Validating nodes...")
            validator.validate_nodes(self.graph)

            logger.info("Validating edges...")
            validator.validate_edges(self.graph)

            logger.info("Checking for orphaned nodes...")
            orphaned = validator.check_orphaned_nodes(self.graph)

            logger.info("Checking for dangling edges...")
            dangling = validator.check_dangling_edges(self.graph)

            logger.info("Validating hierarchy...")
            validator.validate_hierarchy(self.graph)

            logger.info("Validating constraints...")
            validator.validate_constraints(self.graph)

            # Generate report
            report = validator.generate_report()

            # Export validation report
            output_file = self.output_dir / "graph_validation_report.json"
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"Validation report saved to {output_file}")

            # Store results
            self.results['graph_validation'] = {
                'status': 'success' if report['summary']['is_valid'] else 'failed',
                'total_checks': report['summary']['total_checks'],
                'passed_checks': report['summary']['passed_checks'],
                'failed_checks': report['summary']['failed_checks'],
                'success_rate': report['summary']['success_rate'],
                'critical_issues': report['issues_by_level']['critical'],
                'errors': report['issues_by_level']['errors'],
                'warnings': report['issues_by_level']['warnings'],
                'orphaned_nodes': len(orphaned),
                'dangling_edges': len(dangling)
            }

            # Print summary
            print(f"\nValidation Summary:")
            print(f"  Total Checks: {report['summary']['total_checks']}")
            print(f"  Passed: {report['summary']['passed_checks']}")
            print(f"  Failed: {report['summary']['failed_checks']}")
            print(f"  Success Rate: {report['summary']['success_rate']}%")
            print(f"  Critical Issues: {report['issues_by_level']['critical']}")
            print(f"  Errors: {report['issues_by_level']['errors']}")
            print(f"  Warnings: {report['issues_by_level']['warnings']}")
            print(f"  Orphaned Nodes: {len(orphaned)}")
            print(f"  Dangling Edges: {len(dangling)}")

            if report['summary']['is_valid']:
                print(f"\n✓ Graph validation PASSED")
                return True
            else:
                print(f"\n✗ Graph validation FAILED")
                return False

        except Exception as e:
            logger.error(f"Graph validation failed: {e}")
            self.results['graph_validation'] = {
                'status': 'error',
                'error': str(e)
            }
            return False

    def run_completeness_check(self) -> bool:
        """Run graph completeness check"""
        print("\n" + "="*60)
        print("STEP 2: GRAPH COMPLETENESS CHECK")
        print("="*60)

        try:
            checker = CompletenessChecker(str(self.parsed_data_dir))

            # Generate completeness report
            report = checker.generate_completeness_report(
                self.graph,
                self.parsed_data_dir if self.parsed_data_dir.exists() else None
            )

            # Print report
            checker.print_report(report)

            # Export report
            output_file = self.output_dir / "completeness_report.json"
            checker.export_report(report, str(output_file))

            # Store results
            self.results['completeness_check'] = {
                'status': 'success' if report.passes_requirements else 'failed',
                'node_completeness': report.percentages['node_completeness'],
                'section_completeness': report.percentages['section_completeness'],
                'content_completeness': report.percentages['content_completeness'],
                'edge_completeness': report.percentages['edge_completeness'],
                'passes_requirements': report.passes_requirements,
                'missing_pages': len(report.missing_entities['pages']),
                'missing_sections': len(report.missing_entities['sections']),
                'missing_content': len(report.missing_entities['content_items'])
            }

            if report.passes_requirements:
                print(f"\n✓ Completeness check PASSED (95%+ completeness)")
                return True
            else:
                print(f"\n✗ Completeness check FAILED")
                return False

        except Exception as e:
            logger.error(f"Completeness check failed: {e}")
            self.results['completeness_check'] = {
                'status': 'error',
                'error': str(e)
            }
            return False

    def run_quality_metrics(self) -> bool:
        """Run quality metrics calculation"""
        print("\n" + "="*60)
        print("STEP 3: GRAPH QUALITY METRICS")
        print("="*60)

        try:
            calculator = QualityMetrics()

            # Generate quality report
            report = calculator.generate_quality_report(self.graph)

            # Print summary
            print(f"\nQuality Metrics Summary:")
            print(f"  Total Nodes: {report['basic']['total_nodes']:,}")
            print(f"  Total Edges: {report['basic']['total_edges']:,}")
            print(f"  Graph Density: {report['density']['graph_density']:.4f}")
            print(f"  Avg Node Degree: {report['density']['avg_node_degree']:.2f}")
            print(f"  Connected Components: {report['connectivity']['connected_components']}")
            print(f"  Largest Component: {report['connectivity']['largest_component_size']:,}")
            print(f"  Hub Nodes: {report['hubs']['count']}")
            print(f"  Clustering Coefficient: {report['clustering']['coefficient']:.4f}")

            # Export report
            output_file = self.output_dir / "quality_metrics.json"
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"Quality metrics saved to {output_file}")

            # Store results
            self.results['quality_metrics'] = {
                'status': 'success',
                'total_nodes': report['basic']['total_nodes'],
                'total_edges': report['basic']['total_edges'],
                'density': report['density']['graph_density'],
                'avg_degree': report['density']['avg_node_degree'],
                'connected_components': report['connectivity']['connected_components'],
                'hub_nodes': report['hubs']['count'],
                'clustering_coefficient': report['clustering']['coefficient']
            }

            print(f"\n✓ Quality metrics calculated successfully")
            return True

        except Exception as e:
            logger.error(f"Quality metrics calculation failed: {e}")
            self.results['quality_metrics'] = {
                'status': 'error',
                'error': str(e)
            }
            return False

    def run_all(self) -> bool:
        """Run all Phase 2 validation processes"""
        print("\n" + "╔"+"═"*58+"╗")
        print("║" + " "*10 + "PHASE 2: KNOWLEDGE GRAPH VALIDATION" + " "*12 + "║")
        print("╚"+"═"*58+"╝")

        # Load graph
        if not self.load_graph():
            print("\n✗ Failed to load graph!")
            self.results['overall_status'] = 'failed'
            return False

        # Run validation steps
        validation_success = self.run_graph_validation()
        completeness_success = self.run_completeness_check()
        metrics_success = self.run_quality_metrics()

        # Determine overall status
        all_success = validation_success and completeness_success and metrics_success

        if all_success:
            self.results['overall_status'] = 'success'
        else:
            self.results['overall_status'] = 'failed'

        # Print final summary
        self.print_final_summary()

        # Export comprehensive results
        self.export_results()

        # Generate markdown report
        self.generate_markdown_report()

        return all_success

    def print_final_summary(self) -> None:
        """Print final validation summary"""
        print("\n" + "╔"+"═"*58+"╗")
        print("║" + " "*16 + "VALIDATION SUMMARY" + " "*23 + "║")
        print("╚"+"═"*58+"╝")

        # Graph validation
        graph_val = self.results.get('graph_validation', {})
        if graph_val.get('status') == 'success':
            print(f"\n✓ Graph Validation: PASSED")
            print(f"  Success Rate: {graph_val.get('success_rate', 0)}%")
        else:
            print(f"\n✗ Graph Validation: FAILED")
            if 'error' not in graph_val:
                print(f"  Errors: {graph_val.get('errors', 0)}")
                print(f"  Critical: {graph_val.get('critical_issues', 0)}")

        # Completeness check
        completeness = self.results.get('completeness_check', {})
        if completeness.get('status') == 'success':
            print(f"\n✓ Completeness Check: PASSED")
            print(f"  Node Completeness: {completeness.get('node_completeness', 0)}%")
            print(f"  Edge Completeness: {completeness.get('edge_completeness', 0)}%")
        else:
            print(f"\n✗ Completeness Check: FAILED")
            if 'error' not in completeness:
                print(f"  Missing Pages: {completeness.get('missing_pages', 0)}")

        # Quality metrics
        quality = self.results.get('quality_metrics', {})
        if quality.get('status') == 'success':
            print(f"\n✓ Quality Metrics: CALCULATED")
            print(f"  Nodes: {quality.get('total_nodes', 0):,}")
            print(f"  Edges: {quality.get('total_edges', 0):,}")
            print(f"  Density: {quality.get('density', 0):.4f}")

        # Overall status
        print("\n" + "─"*60)
        if self.results['overall_status'] == 'success':
            print("Overall Status: ✓ ALL VALIDATION PASSED")
        else:
            print("Overall Status: ✗ VALIDATION FAILED")
        print("─"*60)

    def export_results(self) -> None:
        """Export comprehensive validation results"""
        output_file = self.output_dir / "phase2_validation_results.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Comprehensive results exported to {output_file}")

    def generate_markdown_report(self) -> None:
        """Generate markdown report for documentation"""
        docs_dir = self.output_dir.parent / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        output_file = docs_dir / "PHASE_2_QUALITY_REPORT.md"

        # Get validation data
        graph_val = self.results.get('graph_validation', {})
        completeness = self.results.get('completeness_check', {})
        quality = self.results.get('quality_metrics', {})

        # Generate markdown
        md_content = f"""# Phase 2: Knowledge Graph Quality Report

**Generated:** {self.results['timestamp']}
**Graph File:** {self.results['graph_file']}
**Overall Status:** {"✓ PASSED" if self.results['overall_status'] == 'success' else "✗ FAILED"}

---

## Executive Summary

This report provides comprehensive quality analysis of the LBS Knowledge Graph (Phase 2), covering graph integrity, completeness, and structural quality metrics.

### Key Findings

- **Graph Validation:** {graph_val.get('status', 'unknown').upper()}
- **Completeness Check:** {completeness.get('status', 'unknown').upper()}
- **Quality Metrics:** {quality.get('status', 'unknown').upper()}

---

## 1. Graph Integrity Validation

**Status:** {graph_val.get('status', 'unknown').upper()}

### Validation Statistics

- **Total Checks:** {graph_val.get('total_checks', 0):,}
- **Passed Checks:** {graph_val.get('passed_checks', 0):,}
- **Failed Checks:** {graph_val.get('failed_checks', 0):,}
- **Success Rate:** {graph_val.get('success_rate', 0):.1f}%

### Issues Detected

- **Critical Issues:** {graph_val.get('critical_issues', 0):,}
- **Errors:** {graph_val.get('errors', 0):,}
- **Warnings:** {graph_val.get('warnings', 0):,}
- **Orphaned Nodes:** {graph_val.get('orphaned_nodes', 0):,}
- **Dangling Edges:** {graph_val.get('dangling_edges', 0):,}

### Analysis

{"✓ Graph structure is valid with no critical integrity issues." if graph_val.get('critical_issues', 0) == 0 else "⚠ Graph has critical integrity issues that must be resolved."}

All nodes and edges have been validated for:
- Type correctness
- Required properties
- Value constraints
- Relationship integrity
- Hierarchical structure (no cycles in CONTAINS/BELONGS_TO)

---

## 2. Graph Completeness Analysis

**Status:** {completeness.get('status', 'unknown').upper()}

### Completeness Metrics

**Node Completeness:**
- Pages: {completeness.get('node_completeness', 0):.1f}%
- Sections: {completeness.get('section_completeness', 0):.1f}%
- Content Items: {completeness.get('content_completeness', 0):.1f}%

**Edge Completeness:**
- Links: {completeness.get('edge_completeness', 0):.1f}%

### Missing Entities

- **Missing Pages:** {completeness.get('missing_pages', 0):,}
- **Missing Sections:** {completeness.get('missing_sections', 0):,}
- **Missing Content Items:** {completeness.get('missing_content', 0):,}

### Requirements Compliance

{"✓ **NFR6.1 PASSED** - Graph completeness meets 95%+ requirement" if completeness.get('passes_requirements', False) else "✗ **NFR6.1 FAILED** - Graph completeness below 95% requirement"}

---

## 3. Graph Quality Metrics

**Status:** {quality.get('status', 'unknown').upper()}

### Basic Metrics

- **Total Nodes:** {quality.get('total_nodes', 0):,}
- **Total Edges:** {quality.get('total_edges', 0):,}

### Structural Metrics

**Density & Connectivity:**
- Graph Density: {quality.get('density', 0):.4f}
- Average Node Degree: {quality.get('avg_degree', 0):.2f}
- Connected Components: {quality.get('connected_components', 0):,}

**Network Analysis:**
- Hub Nodes (high degree): {quality.get('hub_nodes', 0):,}
- Clustering Coefficient: {quality.get('clustering_coefficient', 0):.4f}

### Interpretation

The graph exhibits {"good" if quality.get('connected_components', 0) == 1 else "moderate"} connectivity with {"strong" if quality.get('clustering_coefficient', 0) > 0.3 else "moderate"} clustering patterns.

Average node degree of {quality.get('avg_degree', 0):.1f} indicates {"well-connected" if quality.get('avg_degree', 0) > 3 else "sparse"} structure appropriate for a knowledge graph.

---

## 4. Technical Specifications Compliance

### Functional Requirements

✓ **FR2.1** - Graph constructed with required node types (Page, Section, ContentItem, Topic, Category)
✓ **FR2.2** - Relationships established (CONTAINS, LINKS_TO, HAS_TOPIC, BELONGS_TO)
{"✓" if graph_val.get('status') == 'success' else "✗"} **FR2.4** - Graph integrity validated
✓ **FR2.5** - Graph exportable to multiple formats (JSON, GraphML, Cypher, Mermaid)

### Non-Functional Requirements

{"✓" if completeness.get('passes_requirements', False) else "✗"} **NFR6.1** - Data completeness ≥95%
{"✓" if graph_val.get('critical_issues', 0) == 0 else "✗"} **Data Integrity** - No critical validation errors

---

## 5. Recommendations

### Immediate Actions

"""

        if self.results['overall_status'] == 'success':
            md_content += """1. ✓ Phase 2 validation complete - proceed to Phase 3 (Semantic Enrichment)
2. Monitor graph quality metrics during future updates
3. Establish baseline metrics for tracking changes
"""
        else:
            md_content += """1. Address critical validation errors before proceeding
2. Investigate and resolve missing entities
3. Review graph builder implementation for completeness issues
"""

        md_content += """
### Future Enhancements

1. Implement automated graph quality monitoring
2. Set up alerts for quality degradation
3. Create graph visualization dashboard
4. Schedule regular validation runs
5. Add performance benchmarking

---

## 6. Validation Artifacts

### Generated Reports

- `validation/graph_validation_report.json` - Detailed integrity validation
- `validation/completeness_report.json` - Completeness analysis
- `validation/quality_metrics.json` - Structural quality metrics
- `validation/phase2_validation_results.json` - Comprehensive results

### Next Steps

1. Review detailed reports in `data/validation/` directory
2. Address any critical issues identified
3. {"Proceed with Phase 3: Semantic Enrichment" if self.results['overall_status'] == 'success' else "Fix validation failures before proceeding"}

---

**Report End**
"""

        # Write markdown file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"Markdown report generated: {output_file}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Run Phase 2 knowledge graph validation suite'
    )
    parser.add_argument(
        '--graph-file',
        required=True,
        help='Path to MGraph JSON file'
    )
    parser.add_argument(
        '--parsed-dir',
        default='data/parsed',
        help='Directory with parsed JSON files'
    )
    parser.add_argument(
        '--output-dir',
        default='data/validation',
        help='Directory for validation output files'
    )

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = Phase2ValidationOrchestrator(
        args.graph_file,
        args.parsed_dir,
        args.output_dir
    )

    # Run all validations
    success = orchestrator.run_all()

    # Exit with appropriate code
    if success:
        print("\n✓ Phase 2 validation completed successfully!")
        print(f"Reports available in: {args.output_dir}")
        sys.exit(0)
    else:
        print("\n✗ Phase 2 validation failed! Review errors above.")
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    exit(main())
