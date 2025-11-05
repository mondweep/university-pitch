"""
Analysis module for pattern recognition and extraction validation.

This module provides tools for:
- Pattern analysis across crawled content
- Extraction validation and accuracy metrics
- Ground truth dataset creation
"""

from .pattern_analyzer import PatternAnalyzer, PatternReport
from .extraction_validator import ExtractionValidator, ValidationReport
from .ground_truth import GroundTruthBuilder, GroundTruthDataset

__all__ = [
    'PatternAnalyzer',
    'PatternReport',
    'ExtractionValidator',
    'ValidationReport',
    'GroundTruthBuilder',
    'GroundTruthDataset',
]
