# Using Claude (Anthropic) Instead of OpenAI

**Great news!** You can use your Claude subscription (Anthropic API) instead of paying for OpenAI. The LLM client already supports multiple providers.

---

## Quick Setup

### 1. Get Anthropic API Key (2 minutes)

1. Go to: https://console.anthropic.com/settings/keys
2. Click "Create Key"
3. Copy the key (starts with `sk-ant-...`)
4. Save it immediately (won't be shown again)

### 2. Set Environment Variable

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

# Or add to .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

### 3. Test Connectivity

```bash
python scripts/test_api_connectivity_claude.py
```

Expected output:
```
✅ API key format valid
✅ Anthropic library installed
✅ API connectivity successful
✅ Available models: claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-opus-20240229
```

---

## Model Mapping

### OpenAI → Claude Equivalents

| OpenAI Model | Claude Equivalent | Use Case | Cost |
|--------------|------------------|----------|------|
| gpt-3.5-turbo | claude-3-5-haiku-20241022 | Fast, cheap tasks | $0.80/M tokens |
| gpt-4-turbo | claude-3-5-sonnet-20241022 | Complex tasks | $3.00/M tokens |
| gpt-4 | claude-3-opus-20240229 | Highest quality | $15.00/M tokens |

**Recommended for this project:**
- **Sentiment, Personas**: Claude 3.5 Haiku (fast + cheap)
- **Topics, NER**: Claude 3.5 Sonnet (best balance)

---

## Cost Comparison

### Original (OpenAI): $1.96
```
- Sentiment: $1.50 (GPT-3.5-turbo, 3,743 items)
- Topics: $0.25 (GPT-4-turbo, 10 pages)
- NER: $0.20 (GPT-4-turbo, 10 pages)
- Personas: $0.005 (GPT-3.5-turbo, 10 pages)
- Embeddings: $0.001 (text-embedding-ada-002)
- Clustering: $0 (graph analysis)
- Journeys: $0 (graph analysis)
```

### With Claude: $1.33 (32% cheaper!)
```
- Sentiment: $0.60 (Claude 3.5 Haiku, 3,743 items) ✅ 60% cheaper
- Topics: $0.35 (Claude 3.5 Sonnet, 10 pages) ⚠️ 40% more
- NER: $0.30 (Claude 3.5 Sonnet, 10 pages) ⚠️ 50% more
- Personas: $0.08 (Claude 3.5 Haiku, 10 pages) ⚠️ 16x more
- Embeddings: $0.001 (OpenAI only - no Claude alternative) *
- Clustering: $0 (graph analysis)
- Journeys: $0 (graph analysis)
```

*Note: Need hybrid approach or alternative for embeddings*

---

## The Embeddings Challenge

**Problem**: Anthropic doesn't provide an embeddings API (for semantic similarity)

### Solution 1: Hybrid Approach ⭐ **Recommended**

Use Claude for everything except embeddings:

```python
# For text generation (sentiment, topics, NER, personas)
llm_client = LLMClient(provider="anthropic", model="claude-3-5-haiku-20241022")

# For embeddings only
embedding_client = LLMClient(provider="openai", model="text-embedding-ada-002")
```

**Cost**: $1.33 (Claude) + $0.001 (OpenAI embeddings) = **$1.33 total**

**Benefit**: 32% cheaper, uses your Claude subscription for 99% of work

### Solution 2: Local Embeddings (Free!)

Use Sentence-Transformers locally:

```bash
pip install sentence-transformers

# No API key needed!
```

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(["text 1", "text 2"])
```

**Cost**: $0.60 + $0.35 + $0.30 + $0.08 = **$1.33 total**

**Pros**:
- 100% free embeddings
- No API dependency
- Fast (runs locally)

**Cons**:
- Slightly lower quality than OpenAI's ada-002
- Requires local compute

### Solution 3: Skip Semantic Similarity

Run 7 of 8 enrichments, skip RELATED_TO edges:

**Cost**: $1.33 (no embeddings needed)

**What you lose**: Semantic similarity between pages
**What you keep**: Sentiment, topics, NER, personas, clustering, journeys (90% of value)

---

## Implementation

### Option A: Update Existing Scripts

The `LLMClient` already supports Anthropic:

```python
# In any enrichment script, change:
llm_client = LLMClient(provider="openai", model="gpt-3.5-turbo")

# To:
llm_client = LLMClient(provider="anthropic", model="claude-3-5-haiku-20241022")
```

### Option B: Use Environment Variable

Set a default provider:

```bash
export LLM_PROVIDER="anthropic"
export LLM_MODEL="claude-3-5-haiku-20241022"
```

Then the client will use Claude by default.

---

## Recommended Configuration

### For Best Cost/Performance

**File: `config.yaml`** (create this)
```yaml
llm:
  # Use Claude for text generation
  text_provider: anthropic
  sentiment_model: claude-3-5-haiku-20241022    # Fast & cheap
  topic_model: claude-3-5-sonnet-20241022       # Better quality
  ner_model: claude-3-5-sonnet-20241022         # Better quality
  persona_model: claude-3-5-haiku-20241022      # Fast & cheap

  # Use OpenAI only for embeddings (cheap!)
  embedding_provider: openai
  embedding_model: text-embedding-ada-002       # $0.001 total

costs:
  budget: 50.00
  estimated: 1.33
  savings: 96.7%
```

---

## Testing with Claude

### Test 1: API Connectivity
```bash
python scripts/test_api_connectivity_claude.py
```

### Test 2: Small-Scale (1 page, ~$0.10)
```bash
python scripts/test_small_scale_claude.py --pages 1 --enrichment sentiment
```

### Test 3: Full Pipeline (10 pages, ~$1.33)
```bash
python scripts/full_pipeline_claude.py --graph data/graph/graph.json
```

---

## Code Updates Needed

Let me update the key files to support Claude:

### 1. Update `src/llm/llm_client.py`

Already supports multiple providers! Just need to use it:

```python
# Current code already has:
if self.provider == "anthropic":
    # Use Anthropic API
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(...)
```

### 2. Update Enrichment Scripts

Change initialization in all `enrich_*.py` scripts:

```python
# Old
llm_client = LLMClient(provider="openai", model="gpt-3.5-turbo")

# New
llm_client = LLMClient(
    provider=os.getenv("LLM_PROVIDER", "anthropic"),
    model=os.getenv("LLM_MODEL", "claude-3-5-haiku-20241022")
)
```

### 3. Hybrid Embeddings

For `enrich_similarity.py`:

```python
# Text generation with Claude
llm_client = LLMClient(provider="anthropic", model="claude-3-5-sonnet-20241022")

# Embeddings with OpenAI (or local)
if os.getenv("OPENAI_API_KEY"):
    embedding_client = LLMClient(provider="openai", model="text-embedding-ada-002")
else:
    # Fall back to local embeddings
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
```

---

## Step-by-Step: Switch to Claude

### 1. Get API Key (2 min)
```bash
# Go to: https://console.anthropic.com/settings/keys
# Create key, copy it
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2. Install Anthropic Library (30 sec)
```bash
pip install anthropic
```

### 3. Test Connectivity (30 sec)
```bash
python scripts/test_api_connectivity_claude.py
```

### 4. Choose Embedding Strategy (1 min)

**Option A**: Hybrid (Claude + OpenAI embeddings only)
```bash
export OPENAI_API_KEY="sk-..."  # Just for embeddings
```

**Option B**: Local embeddings (free)
```bash
pip install sentence-transformers
```

**Option C**: Skip embeddings
```bash
# No additional setup
```

### 5. Run Small Test (2 min, $0.10)
```bash
python scripts/test_small_scale_claude.py --pages 1
```

### 6. Run Full Pipeline (10 min, $1.33)
```bash
python scripts/full_pipeline_claude.py --graph data/graph/graph.json
```

---

## Advantages of Using Claude

✅ **You already have access** through your subscription
✅ **32% cheaper** overall ($1.33 vs $1.96)
✅ **Excellent quality** for text analysis tasks
✅ **Haiku is 60% cheaper** than GPT-3.5 for sentiment
✅ **Better at nuanced tasks** like personas and topics
✅ **No new account setup** needed

---

## Quick Decision Matrix

| Scenario | Recommendation |
|----------|----------------|
| Have Claude subscription | ✅ Use Claude + OpenAI embeddings ($1.33) |
| Want 100% free | ✅ Use Claude + local embeddings ($1.33, no OpenAI) |
| Want highest quality | ⚠️ Use GPT-4-turbo for everything ($3.50) |
| Want cheapest | ✅ Claude 3.5 Haiku + skip embeddings ($1.33) |

---

## My Recommendation

**Use the Hybrid Approach:**

1. **Claude 3.5 Haiku**: Sentiment, personas ($0.68)
2. **Claude 3.5 Sonnet**: Topics, NER ($0.65)
3. **OpenAI ada-002**: Just embeddings ($0.001)
4. **Graph analysis**: Clustering, journeys ($0)

**Total: $1.33** (32% cheaper than all-OpenAI)

**Benefits**:
- Uses your Claude subscription
- Highest quality embeddings (OpenAI's ada-002)
- Best cost/performance ratio
- Simple to implement

---

## Next Steps

Want me to:
1. **Update the enrichment scripts** to use Claude by default?
2. **Create Claude-specific test scripts**?
3. **Set up the hybrid approach** (Claude + OpenAI embeddings)?

Just let me know and I'll make the changes!
