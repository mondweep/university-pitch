# LBS Knowledge Graph - Pattern Analysis Report

**Generated:** 2025-11-05 15:25:46

---

## Executive Summary

This report analyzes content patterns from the London Business School website crawl and validates
the accuracy of domain model extractors.

### Key Metrics

- **Total Pages Analyzed:** 10
- **Page Classification Accuracy:** 30.0%
- **Section Detection Accuracy:** 0.0%
- **Content Extraction Accuracy:** 0.0%
- **Overall F1 Score:** 33.3%

---

## 1. Pattern Analysis Results

### 1.1 Page Type Distribution

| Page Type | Count | Percentage |
|-----------|-------|------------|
| news | 2 | 20.0% |
| about | 1 | 10.0% |
| faculty | 1 | 10.0% |
| event | 1 | 10.0% |
| other | 1 | 10.0% |
| alumni | 1 | 10.0% |
| contact | 1 | 10.0% |
| programme | 1 | 10.0% |
| homepage | 1 | 10.0% |


### 1.2 Section Type Patterns

Top section types identified:

- **other**: 30 occurrences
- **header**: 10 occurrences
- **footer**: 10 occurrences


### 1.3 Content Reuse Statistics

- **Unique text blocks:** 505
- **Total text instances:** 1680
- **Reuse ratio:** 3.33x

**Reuse Distribution:**

- Single Use: 251
- Low Reuse 2 5: 139
- Medium Reuse 6 20: 115
- High Reuse 20 Plus: 0


### 1.4 Most Reused Content

Top 5 most reused text blocks:

1. **$ /$ $ /$...** (10 uses)
2. **Skip to main content...** (10 uses)
3. **Give to LBS...** (10 uses)
4. **Newsroom...** (10 uses)
5. **Events...** (10 uses)


---

## 2. Extraction Validation Results

### 2.1 Page Classification

**Metrics:**

- **Accuracy:** 90.0%
- **Precision:** 100.0%
- **Recall:** 100.0%
- **F1 Score:** 100.0%

**Classification Results:**

- True Positives: 9
- False Positives: 0
- False Negatives: 0

### 2.2 Errors and Misclassifications

Total errors found: 0



---

## 3. Recommendations

### 3.1 High Priority Improvements

Based on validation results, the following areas need attention:


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
