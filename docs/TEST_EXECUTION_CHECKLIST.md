# Test Execution Checklist

Use this checklist to track your testing progress through all 4 levels.

---

## Pre-Testing Setup

- [ ] Repository cloned: `/workspaces/university-pitch/lbs-knowledge-graph`
- [ ] In correct directory: `cd lbs-knowledge-graph`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Python version ≥3.9: `python --version`

---

## Level 1: Infrastructure Testing (5 min, $0)

**Status**: ✅ Can run immediately, no API key needed

### 1.1 Unit Tests
- [ ] All tests run: `python -m pytest tests/ -v --tb=short`
- [ ] Result: `134 passed` in green
- [ ] No failures or errors
- [ ] Coverage report generated: `--cov=src --cov-report=html`
- [ ] Coverage ≥90%

### 1.2 Code Quality
- [ ] Linting: `python -m pylint src/ --rcfile=.pylintrc`
- [ ] Score ≥9.0/10
- [ ] Type checking: `python -m mypy src/ --config-file=mypy.ini`
- [ ] No type errors
- [ ] Formatting: `python -m black src/ tests/ --check`
- [ ] Import sorting: `python -m isort src/ tests/ --check-only`

### 1.3 Graph Validation
- [ ] Script runs: `python scripts/validate_graph.py --graph data/graph/graph.json`
- [ ] Graph loads: 3,963 nodes, 3,953 edges
- [ ] All validations pass
- [ ] No orphaned nodes
- [ ] No invalid edges

### 1.4 File Structure
- [ ] Source organized: `ls -R src/`
- [ ] Tests organized: `ls -R tests/`
- [ ] Scripts organized: `ls -R scripts/`
- [ ] Docs organized: `ls -R docs/`
- [ ] Root directory clean: no stray `.py` or `.md` files

**✅ Level 1 Complete** → Proceed to Level 2

---

## Level 2: Integration Testing (15 min, ~$0.25)

**Status**: ⚠️ Requires OpenAI API key

### 2.1 API Key Setup
- [ ] Account created: https://platform.openai.com
- [ ] API key generated: https://platform.openai.com/api-keys
- [ ] Key format valid: starts with `sk-`
- [ ] Environment variable set: `export OPENAI_API_KEY="sk-..."`
- [ ] Billing method added: https://platform.openai.com/account/billing
- [ ] Initial credits available (or payment method active)

### 2.2 API Connectivity
- [ ] Test script runs: `python scripts/test_api_connectivity.py`
- [ ] API key valid ✅
- [ ] Models available ✅ (gpt-3.5-turbo, gpt-4-turbo, text-embedding-ada-002)
- [ ] Test completion successful ✅
- [ ] Embedding API works ✅

### 2.3 Small-Scale Tests

**Test 1: Sentiment (1 page, $0.08)**
- [ ] Command: `python scripts/test_small_scale.py --pages 1 --enrichment sentiment`
- [ ] Processes 40-50 content items
- [ ] Results show positive/neutral/negative distribution
- [ ] Cost ~$0.08
- [ ] Time ~2-3 seconds
- [ ] No errors

**Test 2: Topics (1 page, $0.03)**
- [ ] Command: `python scripts/test_small_scale.py --pages 1 --enrichment topics`
- [ ] Extracts 5-10 topics
- [ ] Relevance scores 0.7-1.0
- [ ] Cost ~$0.03
- [ ] No errors

**Test 3: Multi-enrichment (2 pages, $0.21)**
- [ ] Command: `python scripts/test_small_scale.py --pages 2 --enrichment all`
- [ ] All 8 enrichments complete
- [ ] Graph updated with new nodes/edges
- [ ] Total cost ~$0.21
- [ ] Validation passes

**✅ Level 2 Complete** → Proceed to Level 3

---

## Level 3: Full Pipeline Testing (45 min, ~$1.96)

**Status**: ⚠️ Requires OpenAI API key + budget

### 3.1 Pre-Flight
- [ ] API connectivity verified (from Level 2)
- [ ] Graph backed up: `cp data/graph/graph.json data/graph/graph_backup_$(date +%Y%m%d).json`
- [ ] Cost estimate: `python scripts/cost_estimate.py --graph data/graph/graph.json`
- [ ] Estimated cost ≤$2.00
- [ ] Budget approved: ready to spend ~$1.96

### 3.2 Pipeline Execution
- [ ] Command: `python scripts/full_pipeline.py --graph data/graph/graph.json --output data/graph/graph_enriched.json --checkpoint-dir data/checkpoints --budget 5.00`
- [ ] Stage 1: Load Graph ✅
- [ ] Stage 2: Sentiment Analysis ✅ (~3 min, $1.50)
- [ ] Stage 3: Topic Extraction ✅ (~2 min, $0.25)
- [ ] Stage 4: NER ✅ (~2 min, $0.20)
- [ ] Stage 5: Persona Classification ✅ (~1 min, $0.005)
- [ ] Stage 6: Embedding Generation ✅ (~30s, $0.001)
- [ ] Stage 7: Semantic Similarity ✅ (~10s, $0)
- [ ] Stage 8: Topic Clustering ✅ (~5s, $0)
- [ ] Stage 9: Journey Mapping ✅ (~15s, $0)
- [ ] Stage 10: Validation ✅ (~30s, $0)
- [ ] Stage 11: Export ✅ (~5s, $0)

### 3.3 Validation
- [ ] Command: `python src/validation/run_phase3_validation.py --graph data/graph/graph_enriched.json --ground-truth tests/fixtures/ --output-report docs/validation_results.json`
- [ ] Sentiment accuracy ≥80% ✅
- [ ] Topic precision ≥75% ✅
- [ ] NER precision ≥85% ✅
- [ ] Persona accuracy ≥75% ✅
- [ ] Similarity edges created ✅
- [ ] Clustering successful ✅
- [ ] Journey paths mapped ✅
- [ ] Budget under $50 ✅
- [ ] All 12 acceptance criteria met ✅✅✅

### 3.4 Graph Comparison
- [ ] Command: `python scripts/compare_graphs.py --before data/graph/graph.json --after data/graph/graph_enriched.json`
- [ ] Nodes added: ~124 (topics, entities, personas)
- [ ] Edges added: ~456 (HAS_TOPIC, MENTIONS, TARGETS, RELATED_TO, CHILD_OF, NEXT_STEP)
- [ ] All pages enriched: 10/10 (100%)
- [ ] No errors or warnings

### 3.5 Export Formats
- [ ] JSON export exists: `data/graph/graph_enriched.json`
- [ ] GraphML export: `data/graph/graph_enriched.graphml`
- [ ] Cypher export: `data/graph/graph_enriched.cypher`
- [ ] Mermaid export: `data/graph/graph_enriched.mermaid`
- [ ] RDF/Turtle export: `data/graph/graph_enriched.ttl`

**✅ Level 3 Complete** → Proceed to Level 4 (optional)

---

## Level 4: Manual Validation (2-4 hours, $0)

**Status**: ✅ Can run anytime, manual effort

### 4.1 Ground Truth Creation

**Sentiment (50 items, ~30 min)**
- [ ] Generate samples: `python scripts/generate_validation_samples.py --graph data/graph/graph_enriched.json --output tests/fixtures/samples_to_label.json --count 50`
- [ ] Label sentiment: `python scripts/label_sentiment.py`
- [ ] All 50 items labeled
- [ ] Labels saved: `tests/fixtures/ground_truth_sentiment.json`

**Topics (10 pages, ~45 min)**
- [ ] Label topics: `python scripts/label_topics.py`
- [ ] All 10 pages labeled
- [ ] Labels saved: `tests/fixtures/ground_truth_topics.json`

**NER (10 pages, ~30 min)**
- [ ] Label entities: `python scripts/label_ner.py`
- [ ] All entities verified
- [ ] Labels saved: `tests/fixtures/ground_truth_ner.json`

**Personas (10 pages, ~20 min)**
- [ ] Label personas: `python scripts/label_personas.py`
- [ ] All 10 pages labeled
- [ ] Labels saved: `tests/fixtures/ground_truth_personas.json`

### 4.2 Accuracy Calculation
- [ ] Command: `python scripts/calculate_accuracy.py --predictions data/graph/graph_enriched.json --ground-truth tests/fixtures/ --output docs/accuracy_report.json`
- [ ] Sentiment: Accuracy, Precision, Recall, F1 calculated
- [ ] Topics: Precision, Recall, MAP calculated
- [ ] NER: Per-type metrics calculated
- [ ] Personas: Multi-label metrics calculated
- [ ] Report saved: `docs/accuracy_report.json`

### 4.3 Qualitative Review
- [ ] Export samples: `python scripts/export_review_samples.py --graph data/graph/graph_enriched.json --output docs/review_samples.html --samples 20`
- [ ] HTML file opens in browser
- [ ] Topics make sense for each page ✅
- [ ] Entities are correct and well-typed ✅
- [ ] Personas align with content ✅
- [ ] Related pages are similar ✅
- [ ] Sentiment matches tone ✅
- [ ] Journey paths are logical ✅

### 4.4 Error Analysis
- [ ] False positives identified and documented
- [ ] False negatives identified and documented
- [ ] Prompt refinements proposed
- [ ] Threshold adjustments proposed
- [ ] Re-run plan created (if needed)

**✅ Level 4 Complete** → Production ready!

---

## Final Checklist

### Documentation
- [ ] All tests documented
- [ ] Results saved to `docs/`
- [ ] Accuracy reports generated
- [ ] Error analysis complete
- [ ] Lessons learned documented

### Code Quality
- [ ] All tests pass (134/134)
- [ ] Code quality ≥9.0/10
- [ ] No type errors
- [ ] No security warnings

### Graph Quality
- [ ] All 10 pages enriched (100%)
- [ ] All acceptance criteria met (12/12)
- [ ] Budget under limit ($1.96 of $50)
- [ ] Accuracy meets targets (75-85%+)

### Production Readiness
- [ ] Graph exported to all formats
- [ ] Validation reports complete
- [ ] Deployment guide reviewed: `docs/DEPLOYMENT_GUIDE.md`
- [ ] AWS infrastructure planned
- [ ] CI/CD workflows ready

---

## Next Steps

**All checklists complete?** → Choose your path:

1. **Phase 4: API + Frontend** - Build REST API and React interface
2. **Production Deployment** - Deploy to AWS with Lambda + S3
3. **Ground Truth Expansion** - Label more examples for higher accuracy
4. **Model Refinement** - Tune prompts and thresholds based on errors

---

## Time & Cost Summary

| Level | Description | Time | Cost | Status |
|-------|-------------|------|------|--------|
| 1 | Infrastructure | 5 min | $0 | ✅ |
| 2 | Integration | 15 min | $0.25 | ⚠️ |
| 3 | Full Pipeline | 45 min | $1.96 | ⚠️ |
| 4 | Manual Validation | 2-4 hrs | $0 | ✅ |
| **Total** | | **~3 hrs** | **$2.21** | |

**Excellent ROI**: ~3 hours and $2 to fully validate a production-ready knowledge graph! 🚀

---

## Support

**Stuck?** See troubleshooting section in:
- `docs/TESTING_GUIDE.md` - Comprehensive testing guide
- `docs/PHASE_3_VALIDATION_REPORT.md` - Detailed validation procedures
- `docs/DEPLOYMENT_GUIDE.md` - Production deployment help

**Questions?** Check the documentation in `docs/` or review completion reports in the project root.
