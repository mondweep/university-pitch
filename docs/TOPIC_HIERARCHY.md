# Topic Hierarchy Report

**Generated:** 2025-11-06 21:51:35

---

## Summary

✅ **Pipeline Status:** COMPLETE

- **Duration:** 0.08 seconds
- **Clusters Created:** 3
- **Average Cluster Size:** 3.33 topics
- **Average Coherence:** 0.733
- **Hierarchy Edges:** 7 CHILD_OF edges
- **Maximum Depth:** 1 levels
- **Average Confidence:** 0.927

## Generated Files

- `docs/topic_hierarchy.mmd` - mermaid
- `docs/cluster_stats.json` - stats

## Topic Hierarchy Visualization

```mermaid
graph TD
    topic_mba[MBA Programs]:::root
    topic_exec_ed[Executive Education]:::root
    topic_research[Research]:::root
    topic_leadership[Leadership Development]:::level1
    topic_finance[Finance]:::level1
    topic_strategy[Business Strategy]:::level1
    topic_marketing[Marketing]:::level1
    topic_innovation[Innovation]:::level1
    topic_faculty[Faculty]:::level1
    topic_entrepreneurship[Entrepreneurship]:::level1
    topic_mba -->|0.91| topic_leadership
    topic_mba -->|0.91| topic_finance
    topic_mba -->|0.91| topic_strategy
    topic_mba -->|0.91| topic_marketing
    topic_exec_ed -->|0.85| topic_innovation
    topic_research -->|1.00| topic_faculty
    topic_research -->|1.00| topic_entrepreneurship

    classDef root fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px
    classDef level1 fill:#4ecdc4,stroke:#0e918c,stroke-width:2px
    classDef level2 fill:#95e1d3,stroke:#38ada9,stroke-width:1px
```

## Next Steps

1. Review topic hierarchy and validate relationships
2. Visualize enriched graph using Mermaid rendering
3. Proceed to next Phase 3 enrichments (NER, personas, etc.)
