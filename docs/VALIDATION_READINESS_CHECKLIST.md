# Phase 3 Validation Readiness Checklist

**Date:** 2025-11-06
**Purpose:** Pre-validation readiness assessment and execution guide

---

## ✅ Validation Infrastructure Readiness

### Code Readiness

- [x] **Enrichment Completeness Checker** (`src/validation/enrichment_completeness.py`)
  - Target: ≥95% completeness
  - Features: All enrichment types, database-driven
  - Status: Production-ready

- [x] **Sentiment Validator** (`src/validation/sentiment_validator.py`)
  - Target: ≥80% accuracy
  - Features: Precision, recall, F1, confusion matrix
  - Status: Production-ready

- [x] **Topic Validator** (`src/validation/topic_validator.py`)
  - Target: ≥75% precision
  - Features: Fuzzy matching, topic coverage
  - Status: Production-ready

- [x] **NER Validator** (`src/validation/ner_validator.py`)
  - Target: ≥85% precision
  - Features: Exact match, type accuracy
  - Status: Production-ready

- [x] **Persona Validator** (`src/validation/persona_validator.py`)
  - Target: ≥75% accuracy
  - Features: Multi-label metrics, per-persona analysis
  - Status: Production-ready

- [x] **Cost Validator** (`src/validation/cost_validator.py`)
  - Target: ≤$50 total cost
  - Features: Per-enrichment tracking, budget alerts
  - Status: Production-ready, template created

- [x] **Master Validation Suite** (`src/validation/run_phase3_validation.py`)
  - Features: Orchestrates all validators, aggregated reporting
  - Status: Production-ready

**Infrastructure Score:** 7/7 ✅

---

## ⏸️ Data Readiness

### Required Data

- [ ] **Database Created**
  - Location: `data/lbs_knowledge_graph.db`
  - Status: NOT FOUND
  - Action: `python src/db_utils.py --create-from-graph data/graph/graph.json`

- [ ] **Enriched Graph Data**
  - Current nodes: 3,963
  - Enrichment status: NOT STARTED
  - Required enrichments:
    - [ ] Sentiment analysis (3,743 content items)
    - [ ] Topic extraction (10 pages)
    - [ ] NER (10 pages)
    - [ ] Persona classification (10 pages)
    - [ ] Semantic similarity
    - [ ] Topic clustering
    - [ ] Journey mapping

- [ ] **Ground Truth Datasets**
  - Status: NOT CREATED
  - Required datasets:
    - [ ] Sentiment ground truth (50 labeled items)
    - [ ] Topic ground truth (10 pages with expected topics)
    - [ ] NER ground truth (10 pages with entity annotations)
    - [ ] Persona ground truth (10 pages with persona labels)

- [ ] **Cost Log Data**
  - Template: ✅ Created at `data/llm_cost_log.json`
  - Actual costs: NOT YET RECORDED
  - Action: Update during enrichment execution

**Data Score:** 1/4 (25%) ⏸️

---

## 📋 Prerequisites Checklist

### Environment Setup

- [ ] **OpenAI API Key Configured**
  ```bash
  # Check if key is set
  echo $OPENAI_API_KEY

  # Or create .env file
  cat > .env << EOF
  OPENAI_API_KEY=sk-your-key-here
  EOF
  ```

- [x] **Python Dependencies Installed**
  ```bash
  pip install -r requirements.txt
  ```

- [x] **Project Structure Validated**
  - src/validation/ ✅
  - src/enrichment/ ✅
  - scripts/ ✅
  - data/ ✅

### Database Setup

- [ ] **Create Database from Graph**
  ```bash
  cd lbs-knowledge-graph
  python src/db_utils.py --create-from-graph data/graph/graph.json

  # Verify creation
  ls -lh data/lbs_knowledge_graph.db
  sqlite3 data/lbs_knowledge_graph.db "SELECT COUNT(*) FROM pages"
  ```

### Enrichment Execution

- [ ] **Run Sentiment Enrichment**
  ```bash
  python scripts/enrich_sentiment.py
  # Expected: 15-20 minutes, $1.50
  # Validates: 3,743 content items enriched
  ```

- [ ] **Run Topic Enrichment**
  ```bash
  python scripts/enrich_topics.py
  # Expected: 1-2 minutes, $0.25
  # Validates: 20-30 topics extracted, HAS_TOPIC edges created
  ```

- [ ] **Run NER Enrichment**
  ```bash
  python scripts/enrich_ner.py
  # Expected: 1-2 minutes, $0.20
  # Validates: 20-40 entities extracted, MENTIONS edges created
  ```

- [ ] **Run Persona Enrichment**
  ```bash
  python scripts/enrich_personas.py
  # Expected: 30 seconds, $0.005
  # Validates: 6 persona nodes, 20-30 TARGETS edges
  ```

- [ ] **Run Similarity Enrichment**
  ```bash
  python scripts/enrich_similarity.py
  # Expected: 1 minute, $0.001
  # Validates: ~25 RELATED_TO edges
  ```

- [ ] **Run Topic Clustering**
  ```bash
  python scripts/enrich_topic_clusters.py
  # Expected: 2 minutes, $0
  # Validates: 3-5 clusters, 2-3 hierarchy levels
  ```

- [ ] **Run Journey Mapping**
  ```bash
  python scripts/enrich_journeys.py
  # Expected: 5 minutes, $0
  # Validates: NEXT_STEP edges, journey paths
  ```

**Enrichment Score:** 0/7 (0%) ⏸️

---

## 📊 Ground Truth Creation Guide

### 1. Sentiment Ground Truth (2-3 hours)

**Sample Size:** 50 content items

**Process:**
```bash
# Generate template
python src/validation/sentiment_validator.py --create-template

# Manual labeling required:
# For each content item:
# - Read full text
# - Assign sentiment: positive/neutral/negative
# - Assign polarity score: -1.0 to 1.0
# - Record confidence: 0.0 to 1.0

# Save to: data/ground_truth/sentiment_gt.json
```

**Labeling Guidelines:**
- **Positive:** Achievements, success stories, opportunities
- **Neutral:** Factual information, process descriptions
- **Negative:** Challenges, criticisms, limitations

### 2. Topic Ground Truth (1 hour)

**Sample Size:** 10 pages

**Process:**
```bash
# Generate template
python src/validation/topic_validator.py --create-template

# Manual labeling required:
# For each page:
# - List 3-5 main topics
# - Use consistent terminology
# - Consider hierarchies

# Save to: data/ground_truth/topic_gt.json
```

**Expected Topics:**
- Leadership Development
- Finance & Economics
- Strategy & Innovation
- Entrepreneurship
- Executive Education
- Research Excellence
- Global Business
- Sustainability & ESG

### 3. NER Ground Truth (1-2 hours)

**Sample Size:** 10 pages

**Process:**
```bash
# Generate template
python src/validation/ner_validator.py --create-template

# Manual labeling required:
# For each page:
# - Mark all entities
# - Classify by type: PERSON, ORGANIZATION, LOCATION, CONCEPT
# - Record exact text span

# Save to: data/ground_truth/ner_gt.json
```

**Entity Types:**
- **PERSON:** Names of individuals (faculty, alumni)
- **ORGANIZATION:** Companies, institutions
- **LOCATION:** Geographical entities
- **CONCEPT:** Business concepts, frameworks

### 4. Persona Ground Truth (30 minutes)

**Sample Size:** 10 pages

**Process:**
```bash
# Generate template
python src/validation/persona_validator.py --create-template

# Manual labeling required:
# For each page:
# - Select 1-3 target personas
# - Consider content relevance

# Save to: data/ground_truth/persona_gt.json
```

**Personas:**
- MBA Students
- Executive Education Participants
- PhD Candidates
- Corporate Partners
- Alumni
- Faculty/Researchers

**Ground Truth Score:** 0/4 (0%) ⏸️

---

## 🚀 Validation Execution Steps

### Step 1: Pre-Validation Checks

```bash
cd /workspaces/university-pitch/lbs-knowledge-graph

# Check database exists
ls -lh data/lbs_knowledge_graph.db

# Check enrichment completeness
sqlite3 data/lbs_knowledge_graph.db << EOF
SELECT
  COUNT(*) as total_items,
  SUM(CASE WHEN sentiment IS NOT NULL THEN 1 ELSE 0 END) as with_sentiment,
  SUM(CASE WHEN topics IS NOT NULL THEN 1 ELSE 0 END) as with_topics
FROM content_items;
EOF

# Check ground truth files
ls -lh data/ground_truth/
```

### Step 2: Run Individual Validators (Optional)

```bash
# Test each validator separately
python -m src.validation.sentiment_validator
python -m src.validation.topic_validator
python -m src.validation.ner_validator
python -m src.validation.persona_validator
python -m src.validation.enrichment_completeness
python -m src.validation.cost_validator
```

### Step 3: Run Master Validation Suite

```bash
# Full validation run
python src/validation/run_phase3_validation.py

# Check exit code
if [ $? -eq 0 ]; then
  echo "✅ All validations PASSED"
else
  echo "❌ Some validations FAILED"
fi
```

### Step 4: Review Results

```bash
# View summary
cat data/phase3_validation_results.json | jq '.'

# View detailed results
cat data/phase3_validation_detailed.json | jq '.'

# Check specific metrics
cat data/phase3_validation_results.json | jq '.sentiment_accuracy, .topic_precision, .ner_precision, .persona_accuracy, .completeness_percentage, .total_cost'
```

---

## 📈 Expected Results

### Success Criteria

All of the following must be true:

```json
{
  "sentiment_accuracy": "≥0.80",
  "topic_precision": "≥0.75",
  "ner_precision": "≥0.85",
  "persona_accuracy": "≥0.75",
  "completeness_percentage": "≥0.95",
  "total_cost": "≤50.00",
  "overall_passed": true
}
```

### Sample Passing Output

```
======================================================================
PHASE 3 VALIDATION SUMMARY
======================================================================
Timestamp: 2025-11-06T20:00:00Z
Overall Status: ✅ ALL PASSED
Tests Passed: 6/6
Tests Failed: 0/6

----------------------------------------------------------------------
INDIVIDUAL TEST RESULTS
----------------------------------------------------------------------
✅ PASS  Sentiment Analysis          85.2% accuracy
✅ PASS  Topic Extraction            78.5% precision
✅ PASS  NER                         87.3% precision
✅ PASS  Persona Classification       76.8% accuracy
✅ PASS  Enrichment Completeness      97.2% complete
✅ PASS  Cost Budget                  $1.96 / $50.00

======================================================================
PHASE 3 ACCEPTANCE CRITERIA
======================================================================
✅  Sentiment accuracy ≥80%
✅  Topic precision ≥75%
✅  NER precision ≥85%
✅  Persona accuracy ≥75%
✅  Enrichment completeness ≥95%
✅  Total cost ≤$50

======================================================================
OVERALL VERDICT
======================================================================
✅ Phase 3 meets ALL acceptance criteria
   Ready for production deployment
```

---

## 🔄 Iteration Process

If validation fails:

### 1. Analyze Failures

```bash
# Check which validators failed
cat data/phase3_validation_results.json | jq '.[] | select(.passed == false)'

# Review detailed metrics
cat data/phase3_validation_detailed.json | jq '.'
```

### 2. Common Issues & Solutions

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Sentiment accuracy <80% | Poor prompt design | Refine sentiment prompts |
| Topic precision <75% | Overgeneralized topics | More specific topic extraction |
| NER precision <85% | Entity recognition errors | Improve NER prompts or use specialized model |
| Persona accuracy <75% | Unclear persona targeting | Better persona classification logic |
| Completeness <95% | Incomplete enrichment run | Re-run failed enrichments |
| Cost >$50 | Inefficient batching | Optimize batch sizes |

### 3. Re-Enrichment

```bash
# Re-run specific enrichment
python scripts/enrich_sentiment.py --force-rerun

# Re-validate
python src/validation/run_phase3_validation.py
```

---

## 📊 Progress Tracking

### Current Status

```
Phase 3 Validation Readiness: 33%

Infrastructure:   ████████████████████ 100% (7/7)
Data:            █████                 25% (1/4)
Enrichment:      ░░░░░░░░░░░░░░░░░░░   0% (0/7)
Ground Truth:    ░░░░░░░░░░░░░░░░░░░   0% (0/4)
```

### Timeline Estimate

| Task | Duration | Status |
|------|----------|--------|
| API Key Setup | 5 minutes | ⏸️ Pending |
| Database Creation | 5 minutes | ⏸️ Pending |
| Enrichment Execution | 25-30 minutes | ⏸️ Pending |
| Ground Truth Creation | 2-4 hours | ⏸️ Pending |
| Validation Execution | 5 minutes | ⏸️ Pending |
| Results Review | 30 minutes | ⏸️ Pending |
| **Total** | **4-6 hours** | ⏸️ **Pending** |

---

## ✅ Ready to Proceed?

Use this checklist to determine readiness:

- [x] Validation scripts implemented
- [x] Validation scripts tested locally
- [ ] OpenAI API key configured
- [ ] Database created from graph
- [ ] All enrichment scripts executed
- [ ] Ground truth datasets created
- [ ] Cost log populated
- [ ] Pre-validation checks passed

**Readiness Score:** 2/8 (25%) ⏸️

**Next Action:** Set up OpenAI API key and create database

---

**Document Generated:** 2025-11-06
**Owner:** Quality Validator
**Status:** Living document - update after each step
**Next Review:** After enrichment execution
