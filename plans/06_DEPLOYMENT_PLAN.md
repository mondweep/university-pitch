# Deployment and Infrastructure Plan

## Executive Summary

This document outlines the deployment strategy, infrastructure requirements, and operational procedures for the LBS Semantic Knowledge Graph platform using **MGraph-DB** as the serverless graph database solution.

**Deployment Model:** Cloud-native, serverless-first
**Graph Database:** MGraph-DB (Python-based, in-memory)
**Hosting:** AWS Lambda + ECS hybrid
**CI/CD:** GitHub Actions
**Monitoring:** Prometheus + Grafana
**Estimated Monthly Cost:** $300 - $800 (significantly reduced due to serverless architecture)

---

## 1. Infrastructure Architecture

### 1.1 Serverless-First Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLOUDFLARE CDN                          │
│                     (DDoS Protection, WAF)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS API Gateway                            │
│                  (HTTPS, Rate Limiting)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┴──────────────────┐
           │                                      │
           ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────┐
│  Lambda Functions   │              │ ECS Fargate (Long)  │
│   (Serverless)      │              │  Running Tasks      │
│                     │              │                     │
│  - Graph API        │              │  - Crawler Service  │
│  - Search API       │              │  - Parser Service   │
│  - Query Engine     │              │  - LLM Enrichment   │
│  - MGraph Loader    │              │                     │
│                     │              │  Auto-scaling:      │
│  Cold start: <1s    │              │  Min: 0, Max: 3     │
│  (MGraph optimized) │              │                     │
└─────────────────────┘              └─────────────────────┘
           │                                      │
           └──────────────────┬──────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐     ┌──────────────┐
│  MGraph-DB   │    │ Elasticsearch│     │  Redis       │
│  (In-Memory) │    │  (Search)    │     │  (Cache)     │
│              │    │              │     │              │
│  Loaded from │    │  Serverless  │     │  ElastiCache │
│  S3 on cold  │    │  (OpenSearch)│     │  Serverless  │
│  start       │    │              │     │              │
│              │    │  Pay per use │     │  Pay per use │
└──────────────┘    └──────────────┘     └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │      S3          │
                    │  - Raw HTML      │
                    │  - Parsed JSON   │
                    │  - MGraph Export │
                    │  - Backups       │
                    │  - Static Assets │
                    └──────────────────┘
```

### 1.2 MGraph-DB Deployment Strategy

**Key Advantages:**
- **Serverless-optimized**: Fast cold starts (<1 second)
- **In-memory performance**: O(1) lookups
- **JSON persistence**: Easy S3 integration
- **No database servers**: Zero infrastructure overhead
- **Multi-export formats**: Interoperability with other tools

**Deployment Pattern:**
```python
# Lambda function loads MGraph from S3
import mgraph_db
import boto3
import json

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Load graph from S3 (cached in Lambda memory)
    graph_data = s3.get_object(
        Bucket='lbs-kg-graph',
        Key='graph/latest.json'
    )

    # Initialize MGraph
    graph = mgraph_db.MGraph()
    graph.load_from_json(graph_data['Body'].read())

    # Execute query
    query = event['queryStringParameters']['q']
    results = graph.query(query)

    return {
        'statusCode': 200,
        'body': json.dumps(results.to_dict())
    }
```

---

## 2. Deployment Components

### 2.1 Lambda Functions (Serverless)

**Graph Query Function:**
```yaml
Function: lbs-kg-graph-query
Runtime: Python 3.11
Memory: 2048 MB (for large graphs)
Timeout: 30 seconds
Reserved Concurrency: 10
Environment:
  - GRAPH_BUCKET: lbs-kg-graph
  - GRAPH_KEY: graph/latest.json
  - ENABLE_CACHING: true
```

**Search Function:**
```yaml
Function: lbs-kg-search
Runtime: Python 3.11
Memory: 1024 MB
Timeout: 15 seconds
Integrations:
  - OpenSearch Serverless
  - MGraph-DB (for graph-enhanced search)
```

### 2.2 ECS Fargate (Background Processing)

**Crawler Service:**
```yaml
Service: crawler-service
Launch Type: FARGATE
Task Definition:
  CPU: 512
  Memory: 1024
  Image: lbs-kg-crawler:latest
Schedule: cron(0 2 * * ? *)  # Daily at 2 AM
```

**Graph Builder Service:**
```yaml
Service: graph-builder-service
Launch Type: FARGATE
Task Definition:
  CPU: 1024
  Memory: 2048
  Image: lbs-kg-graph-builder:latest
Trigger: S3 event (content update)
Process:
  1. Load parsed content from S3
  2. Build MGraph-DB graph in memory
  3. Run LLM enrichment
  4. Export to multiple formats (JSON, GraphML, Cypher)
  5. Upload to S3
```

### 2.3 Storage (S3)

**Bucket Structure:**
```
lbs-kg-content/
├── raw/                    # Raw HTML
├── parsed/                 # Parsed JSON
├── graph/
│   ├── latest.json        # Current MGraph JSON
│   ├── latest.graphml     # GraphML export
│   ├── latest.cypher      # Cypher export
│   └── versions/          # Historical versions
├── exports/               # Various export formats
└── backups/              # Daily backups
```

---

## 3. MGraph-DB Integration

### 3.1 Graph Construction Pipeline

```python
from mgraph_db import MGraph, MNode, MEdge
from typing import Dict, List

class LBSGraphBuilder:
    def __init__(self):
        self.graph = MGraph()

    def build_from_content(self, pages: List[Dict]):
        """Build knowledge graph from parsed pages"""

        # Create Page nodes
        for page in pages:
            node = self.graph.add_node(
                node_type='Page',
                data={
                    'id': page['id'],
                    'url': page['url'],
                    'title': page['title'],
                    'type': page['type'],
                    'importance': page.get('importance', 0.5)
                }
            )

        # Create Section and ContentItem nodes
        for page in pages:
            for section in page.get('sections', []):
                section_node = self.graph.add_node(
                    node_type='Section',
                    data=section
                )

                # Create CONTAINS edge
                self.graph.add_edge(
                    from_node=page['id'],
                    to_node=section['id'],
                    edge_type='CONTAINS',
                    data={'order': section['order']}
                )

        # Create Topic nodes and relationships
        for topic in self.extract_topics():
            topic_node = self.graph.add_node(
                node_type='Topic',
                data=topic
            )

        # Create HAS_TOPIC edges from LLM analysis
        self.enrich_with_topics()

        return self.graph

    def export_graph(self, output_dir: str):
        """Export graph in multiple formats"""

        # JSON (for Lambda loading)
        self.graph.save_to_json(f'{output_dir}/graph.json')

        # GraphML (for visualization tools)
        self.graph.export_graphml(f'{output_dir}/graph.graphml')

        # Cypher (for Neo4j import if needed)
        self.graph.export_cypher(f'{output_dir}/graph.cypher')

        # Mermaid (for documentation)
        self.graph.export_mermaid(f'{output_dir}/graph.mmd')
```

### 3.2 Query Patterns with MGraph

```python
# Example queries using MGraph-DB

# Find all pages of a specific type
def get_pages_by_type(graph: MGraph, page_type: str):
    return graph.query(
        node_type='Page',
        filters={'type': page_type}
    )

# Get page with all its content (traversal)
def get_page_with_content(graph: MGraph, page_id: str):
    page = graph.get_node(page_id)

    # Traverse CONTAINS relationships
    sections = graph.traverse(
        start_node=page_id,
        edge_type='CONTAINS',
        depth=2  # Page -> Section -> ContentItem
    )

    return {
        'page': page.data,
        'sections': sections.to_list()
    }

# Find related content by topic
def find_by_topic(graph: MGraph, topic_name: str):
    # Get topic node
    topic = graph.query(
        node_type='Topic',
        filters={'name': topic_name}
    ).first()

    # Find all content with this topic
    return graph.traverse_reverse(
        start_node=topic.id,
        edge_type='HAS_TOPIC'
    )

# Complex query: Pages linking to high-importance pages
def get_important_page_referrers(graph: MGraph, min_importance: float = 0.8):
    important_pages = graph.query(
        node_type='Page',
        filters=lambda p: p['importance'] >= min_importance
    )

    referrers = []
    for page in important_pages:
        refs = graph.traverse_reverse(
            start_node=page.id,
            edge_type='LINKS_TO'
        )
        referrers.extend(refs.to_list())

    return referrers
```

---

## 4. CI/CD Pipeline

### 4.1 Deployment Workflow

**.github/workflows/deploy-lambda.yml:**
```yaml
name: Deploy Lambda Functions

on:
  push:
    branches: [main]
    paths:
      - 'lambda/**'
      - 'requirements.txt'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt -t package/
          cp -r lambda/* package/

      - name: Create deployment package
        run: |
          cd package
          zip -r ../deployment.zip .

      - name: Deploy to Lambda
        run: |
          aws lambda update-function-code \
            --function-name lbs-kg-graph-query \
            --zip-file fileb://deployment.zip
```

### 4.2 Graph Build Pipeline

**.github/workflows/build-graph.yml:**
```yaml
name: Build Knowledge Graph

on:
  schedule:
    - cron: '0 3 * * *'  # Daily at 3 AM (after crawler)
  workflow_dispatch:

jobs:
  build-graph:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: true

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install MGraph-DB
        run: |
          pip install mgraph-db
          pip install -r requirements.txt

      - name: Download content from S3
        run: |
          aws s3 sync s3://lbs-kg-content/parsed ./content/parsed

      - name: Build graph
        run: |
          python scripts/build_graph.py \
            --input ./content/parsed \
            --output ./graph

      - name: Run LLM enrichment
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python scripts/enrich_graph.py \
            --graph ./graph/graph.json \
            --output ./graph/enriched.json

      - name: Upload to S3
        run: |
          aws s3 cp ./graph/enriched.json \
            s3://lbs-kg-content/graph/latest.json

          # Upload exports
          aws s3 cp ./graph/enriched.graphml \
            s3://lbs-kg-content/graph/latest.graphml

          # Backup with timestamp
          TIMESTAMP=$(date +%Y%m%d_%H%M%S)
          aws s3 cp ./graph/enriched.json \
            s3://lbs-kg-content/graph/versions/${TIMESTAMP}.json

      - name: Invalidate CloudFront cache
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CF_DISTRIBUTION_ID }} \
            --paths "/api/*"
```

---

## 5. Monitoring and Operations

### 5.1 Lambda Metrics

**CloudWatch Metrics:**
- `Invocations` - Total invocations
- `Duration` - Execution time
- `Errors` - Error count
- `Throttles` - Throttled requests
- `ConcurrentExecutions` - Concurrent invocations

**Custom Metrics:**
```python
import boto3
cloudwatch = boto3.client('cloudwatch')

def track_graph_query(query_time_ms, result_count):
    cloudwatch.put_metric_data(
        Namespace='LBS-KG',
        MetricData=[
            {
                'MetricName': 'GraphQueryDuration',
                'Value': query_time_ms,
                'Unit': 'Milliseconds'
            },
            {
                'MetricName': 'GraphQueryResults',
                'Value': result_count,
                'Unit': 'Count'
            }
        ]
    )
```

### 5.2 Cost Optimization

**Serverless Advantages:**
- **No idle costs**: Pay only for actual usage
- **Auto-scaling**: Scales to zero when not in use
- **No database servers**: MGraph runs in Lambda memory
- **Reduced data transfer**: S3-based persistence

**Estimated Monthly Costs (Serverless):**

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Lambda (Graph Query) | 100K invocations @ 2s | $20 |
| Lambda (Search) | 50K invocations @ 1s | $10 |
| ECS Fargate (Crawler) | 1 hour/day | $15 |
| ECS Fargate (Graph Builder) | 2 hours/day | $30 |
| S3 Storage | 50GB | $1.15 |
| S3 Requests | 1M requests | $5 |
| OpenSearch Serverless | 4 OCUs | $200 |
| ElastiCache Serverless | 1GB-hour | $15 |
| API Gateway | 1M requests | $3.50 |
| CloudWatch | Logs & Metrics | $15 |
| Cloudflare | Pro Plan | $20 |

**Total: ~$334/month** (vs. $579-959 with traditional architecture)

**LLM API Costs:**
- OpenAI GPT-4: $100-300/month

**Grand Total: $434-634/month** (40% savings)

---

## 6. Deployment Procedures

### 6.1 Initial Deployment

**Step 1: Deploy Infrastructure (Terraform)**
```bash
cd infrastructure/serverless
terraform init
terraform apply
```

**Step 2: Deploy Lambda Functions**
```bash
./scripts/deploy-lambda.sh graph-query
./scripts/deploy-lambda.sh search
./scripts/deploy-lambda.sh admin
```

**Step 3: Build Initial Graph**
```bash
# Run crawler
python scripts/crawler.py --urls urls.txt --output s3://lbs-kg-content/raw

# Parse content
python scripts/parser.py --input s3://lbs-kg-content/raw --output s3://lbs-kg-content/parsed

# Build graph
python scripts/build_graph.py --input s3://lbs-kg-content/parsed --output ./graph

# Upload graph
aws s3 cp ./graph/graph.json s3://lbs-kg-content/graph/latest.json
```

**Step 4: Test Deployment**
```bash
# Test Lambda function
aws lambda invoke \
  --function-name lbs-kg-graph-query \
  --payload '{"queryStringParameters": {"type": "program"}}' \
  response.json

cat response.json
```

### 6.2 Zero-Downtime Updates

```bash
# Update Lambda with alias routing
aws lambda update-function-code \
  --function-name lbs-kg-graph-query \
  --zip-file fileb://deployment.zip \
  --publish

# Create new version
NEW_VERSION=$(aws lambda publish-version \
  --function-name lbs-kg-graph-query \
  --query 'Version' --output text)

# Update alias with traffic shifting
aws lambda update-alias \
  --function-name lbs-kg-graph-query \
  --name production \
  --function-version $NEW_VERSION \
  --routing-config AdditionalVersionWeights={"$PREV_VERSION"=0.1}
```

---

## 7. Backup and Disaster Recovery

### 7.1 Graph Versioning

**S3 Versioning Enabled:**
```bash
aws s3api put-bucket-versioning \
  --bucket lbs-kg-content \
  --versioning-configuration Status=Enabled
```

**Daily Snapshots:**
```bash
# Automated daily backup (Lambda)
def backup_graph():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Copy latest to versioned backup
    s3.copy_object(
        CopySource='lbs-kg-content/graph/latest.json',
        Bucket='lbs-kg-content',
        Key=f'graph/backups/daily/{timestamp}.json'
    )

    # Export to multiple formats for safety
    graph = MGraph.load_from_json('graph/latest.json')
    graph.export_graphml(f'graph/backups/daily/{timestamp}.graphml')
    graph.export_cypher(f'graph/backups/daily/{timestamp}.cypher')
```

### 7.2 Recovery Procedures

**Restore from Backup:**
```bash
# List available backups
aws s3 ls s3://lbs-kg-content/graph/backups/daily/

# Restore specific version
aws s3 cp s3://lbs-kg-content/graph/backups/daily/20251101_020000.json \
  s3://lbs-kg-content/graph/latest.json

# Warm up Lambda (force reload)
aws lambda update-function-configuration \
  --function-name lbs-kg-graph-query \
  --environment Variables={FORCE_RELOAD=true}
```

---

## 8. Security

### 8.1 Lambda Security

- **IAM Roles**: Least-privilege access to S3, CloudWatch
- **VPC**: Optional VPC integration for private resources
- **Environment Variables**: Encrypted with KMS
- **API Gateway**: AWS WAF protection, API keys

### 8.2 Data Security

- **S3 Encryption**: AES-256 at rest
- **TLS**: All data in transit
- **Versioning**: S3 versioning enabled
- **Access Logs**: CloudTrail logging enabled

---

## 9. MGraph-DB Advantages Summary

✅ **Serverless-optimized**: Fast cold starts, minimal overhead
✅ **In-memory performance**: O(1) lookups, fast traversals
✅ **Multi-format export**: JSON, GraphML, Cypher, Mermaid, RDF
✅ **Type-safe**: Runtime validation, schema enforcement
✅ **Python-native**: Easy LLM integration, rich ecosystem
✅ **Cost-effective**: No database servers, pay-per-use
✅ **Interoperable**: Can export to Neo4j, Gephi, other tools
✅ **GenAI-ready**: Designed for knowledge graphs and LLM context

---

**Document Version:** 1.0
**Last Updated:** November 2025
**MGraph-DB Version:** Latest from https://github.com/owasp-sbot/MGraph-DB
