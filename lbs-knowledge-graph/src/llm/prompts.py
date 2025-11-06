"""
Prompt Templates for LLM Enrichment.

Provides optimized prompts for sentiment analysis, topic extraction,
named entity recognition, and other enrichment tasks.
"""

from typing import List, Optional


class PromptTemplates:
    """
    Collection of prompt templates for knowledge graph enrichment.

    All prompts are optimized for:
    - Token efficiency (concise but effective)
    - Consistent JSON output format
    - Batch processing compatibility
    - Cost optimization
    """

    @staticmethod
    def sentiment_analysis(content: str, include_reasoning: bool = False) -> str:
        """
        Generate sentiment analysis prompt.

        Args:
            content: Text content to analyze
            include_reasoning: Whether to include reasoning in output

        Returns:
            Formatted prompt for sentiment analysis
        """
        base_prompt = f"""Analyze the sentiment of the following content.

Content: {content}

Respond with ONLY valid JSON in this format:
{{
  "sentiment": "positive" | "negative" | "neutral",
  "confidence": 0.0-1.0,
  "score": -1.0 to 1.0 (negative to positive)"""

        if include_reasoning:
            base_prompt += """,
  "reasoning": "brief explanation"
}}"""
        else:
            base_prompt += """
}"""

        return base_prompt

    @staticmethod
    def topic_extraction(
        content: str,
        num_topics: int = 5,
        domain: Optional[str] = None
    ) -> str:
        """
        Generate topic extraction prompt.

        Args:
            content: Text content to analyze
            num_topics: Number of topics to extract (3-5 recommended)
            domain: Optional domain context (e.g., 'education', 'technology')

        Returns:
            Formatted prompt for topic extraction
        """
        domain_context = f" in the {domain} domain" if domain else ""

        return f"""Extract the {num_topics} most relevant topics{domain_context} from this content.

Content: {content}

Respond with ONLY valid JSON in this format:
{{
  "topics": [
    {{
      "name": "topic name",
      "confidence": 0.0-1.0,
      "keywords": ["key1", "key2", "key3"]
    }}
  ]
}}

Focus on:
- Main themes and subjects
- Key concepts and ideas
- Relevant keywords
"""

    @staticmethod
    def named_entity_recognition(content: str) -> str:
        """
        Generate named entity recognition prompt.

        Args:
            content: Text content to analyze

        Returns:
            Formatted prompt for NER
        """
        return f"""Extract all named entities from this content.

Content: {content}

Respond with ONLY valid JSON in this format:
{{
  "entities": [
    {{
      "text": "entity text",
      "type": "PERSON" | "ORGANIZATION" | "LOCATION" | "DATE" | "EVENT" | "PRODUCT",
      "confidence": 0.0-1.0
    }}
  ]
}}

Entity types:
- PERSON: People, characters
- ORGANIZATION: Companies, institutions, universities
- LOCATION: Cities, countries, places
- DATE: Dates, times, periods
- EVENT: Named events, conferences
- PRODUCT: Products, services, programs
"""

    @staticmethod
    def persona_classification(content: str, available_personas: List[str]) -> str:
        """
        Generate persona/audience classification prompt.

        Args:
            content: Text content to analyze
            available_personas: List of possible persona types

        Returns:
            Formatted prompt for persona classification
        """
        persona_list = ", ".join([f'"{p}"' for p in available_personas])

        return f"""Classify the target audience/persona for this content.

Content: {content}

Available personas: {persona_list}

Respond with ONLY valid JSON in this format:
{{
  "primary_persona": "most relevant persona from list",
  "secondary_personas": ["other relevant personas"],
  "confidence": 0.0-1.0,
  "characteristics": ["key audience characteristic 1", "characteristic 2"]
}}

Consider:
- Who would benefit most from this content
- Language level and complexity
- Interests and needs addressed
"""

    @staticmethod
    def semantic_similarity(content1: str, content2: str) -> str:
        """
        Generate semantic similarity comparison prompt.

        Args:
            content1: First piece of content
            content2: Second piece of content

        Returns:
            Formatted prompt for similarity analysis
        """
        return f"""Compare the semantic similarity between these two pieces of content.

Content 1: {content1}

Content 2: {content2}

Respond with ONLY valid JSON in this format:
{{
  "similarity_score": 0.0-1.0,
  "semantic_overlap": ["shared concept 1", "shared concept 2"],
  "key_differences": ["difference 1", "difference 2"],
  "relationship": "identical" | "related" | "tangentially_related" | "unrelated"
}}

Consider:
- Shared topics and themes
- Common keywords and concepts
- Contextual meaning
- Overall subject matter
"""

    @staticmethod
    def content_categorization(
        content: str,
        categories: List[str],
        allow_multiple: bool = True
    ) -> str:
        """
        Generate content categorization prompt.

        Args:
            content: Text content to categorize
            categories: List of available categories
            allow_multiple: Whether content can belong to multiple categories

        Returns:
            Formatted prompt for categorization
        """
        category_list = ", ".join([f'"{c}"' for c in categories])
        multi_note = "Can assign multiple categories." if allow_multiple else "Select only ONE category."

        return f"""Categorize this content into the most appropriate category/categories.

Content: {content}

Available categories: {category_list}

{multi_note}

Respond with ONLY valid JSON in this format:
{{
  "categories": [
    {{
      "name": "category name",
      "confidence": 0.0-1.0,
      "reasoning": "brief explanation"
    }}
  ],
  "primary_category": "most relevant category"
}}
"""

    @staticmethod
    def key_insights_extraction(content: str, max_insights: int = 5) -> str:
        """
        Generate key insights extraction prompt.

        Args:
            content: Text content to analyze
            max_insights: Maximum number of insights to extract

        Returns:
            Formatted prompt for insight extraction
        """
        return f"""Extract up to {max_insights} key insights from this content.

Content: {content}

Respond with ONLY valid JSON in this format:
{{
  "insights": [
    {{
      "insight": "concise insight statement",
      "importance": 0.0-1.0,
      "category": "fact" | "opinion" | "recommendation" | "finding" | "trend",
      "evidence": "supporting text from content"
    }}
  ],
  "summary": "one-sentence overall takeaway"
}}

Focus on:
- Novel or important information
- Actionable findings
- Key facts and statistics
- Notable recommendations
- Emerging trends or patterns
"""

    @staticmethod
    def quality_assessment(content: str) -> str:
        """
        Generate content quality assessment prompt.

        Args:
            content: Text content to assess

        Returns:
            Formatted prompt for quality assessment
        """
        return f"""Assess the quality and credibility of this content.

Content: {content}

Respond with ONLY valid JSON in this format:
{{
  "overall_quality": 0.0-1.0,
  "dimensions": {{
    "clarity": 0.0-1.0,
    "accuracy": 0.0-1.0,
    "depth": 0.0-1.0,
    "credibility": 0.0-1.0,
    "relevance": 0.0-1.0
  }},
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "recommendations": ["improvement 1", "improvement 2"]
}}

Evaluate:
- Clarity and readability
- Factual accuracy indicators
- Depth of information
- Source credibility signals
- Relevance to stated topic
"""

    @staticmethod
    def relationship_inference(
        source_content: str,
        target_content: str,
        relationship_types: List[str]
    ) -> str:
        """
        Generate relationship inference prompt for graph edges.

        Args:
            source_content: Source node content
            target_content: Target node content
            relationship_types: Possible relationship types

        Returns:
            Formatted prompt for relationship inference
        """
        rel_types = ", ".join([f'"{r}"' for r in relationship_types])

        return f"""Infer the relationship between these two pieces of content.

Source content: {source_content}

Target content: {target_content}

Possible relationship types: {rel_types}

Respond with ONLY valid JSON in this format:
{{
  "relationship_exists": true | false,
  "relationship_type": "type from list or 'other'",
  "confidence": 0.0-1.0,
  "direction": "source_to_target" | "target_to_source" | "bidirectional",
  "strength": 0.0-1.0,
  "reasoning": "brief explanation"
}}

Consider:
- Logical connections
- Temporal relationships
- Hierarchical structures
- Causal links
- Reference patterns
"""

    @staticmethod
    def batch_wrapper(individual_prompts: List[str]) -> str:
        """
        Wrap multiple individual prompts for batch processing.

        Args:
            individual_prompts: List of individual prompt strings

        Returns:
            Combined batch prompt
        """
        batch_items = []
        for idx, prompt in enumerate(individual_prompts, 1):
            batch_items.append(f"Item {idx}:\n{prompt}")

        return "\n\n".join(batch_items) + """

Process all items above and respond with results in the same order.
Ensure each item gets a separate, complete JSON response.
"""
