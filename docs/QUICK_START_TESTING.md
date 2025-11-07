# Quick Start Testing Guide

**Goal**: Test your LBS Knowledge Graph in 5 minutes, no API key needed!

---

## 1️⃣ Infrastructure Test (2 minutes)

**Run all unit tests:**
```bash
cd /workspaces/university-pitch/lbs-knowledge-graph
python -m pytest tests/ -v --tb=short
```

**Expected**: `134 passed` in green

**If tests fail**, check:
```bash
# Install dependencies
pip install -r requirements.txt

# Try again
python -m pytest tests/ -v
```

---

## 2️⃣ Code Quality (1 minute)

```bash
# Lint
python -m pylint src/ --rcfile=.pylintrc

# Expected: "rated at 9.2/10"

# Type check
python -m mypy src/ --config-file=mypy.ini

# Expected: "Success: no issues found"
```

---

## 3️⃣ Graph Validation (1 minute)

```bash
python scripts/validate_graph.py --graph data/graph/graph.json
```

**Expected output:**
```
✅ Graph loaded successfully
   Nodes: 3,963
   Edges: 3,953
✅ All validations passed
```

---

## 4️⃣ File Structure (30 seconds)

```bash
# Check organization
ls -R src/ tests/ scripts/ docs/

# Verify no files in root
ls *.py 2>/dev/null || echo "✅ Clean root directory"
```

---

## ✅ Success Criteria

- [ ] All 134 tests pass
- [ ] Code quality score ≥9.0/10
- [ ] Graph loads with 3,963 nodes
- [ ] No Python files in root
- [ ] All files organized in subdirectories

---

## 🚀 Next Steps

**All tests passed?** → Ready for integration testing!

1. Get OpenAI API key: https://platform.openai.com/api-keys
2. Set environment variable: `export OPENAI_API_KEY="sk-..."`
3. Run small-scale test: `python scripts/test_small_scale.py --pages 1`

**Tests failed?** → See [TESTING_GUIDE.md](TESTING_GUIDE.md#troubleshooting)

---

## Time Estimate

| Level | Time | Cost | Status |
|-------|------|------|--------|
| Infrastructure | 5 min | $0 | ✅ Can run now |
| Integration (1 page) | 10 min | $0.10 | ⚠️ Needs API key |
| Full pipeline (10 pages) | 45 min | $1.96 | ⚠️ Needs API key |

Total investment: **1 hour, $2** to fully test everything!
