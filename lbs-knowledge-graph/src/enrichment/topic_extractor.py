"""
Topic Extractor for Knowledge Graph Enrichment

Extracts topics from pages and sections using LLM analysis.
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .llm_client import LLMClient
from .topic_models import (
    Topic, TopicRelevance, TopicExtractionResult, TopicCategory,
    TopicTaxonomy, BusinessDiscipline, CrossCuttingTheme
)

logger = logging.getLogger(__name__)


# Topic extraction prompt template
TOPIC_PROMPT = """Extract 3-5 main topics from the following content. Return JSON:

{{
  "topics": [
    {{
      "name": "topic name",
      "relevance": 0.0-1.0,
      "category": "academic|research|student_life|business|alumni|events|admissions|career|faculty|general",
      "description": "brief description"
    }}
  ]
}}

Context: This is a {page_type} page from London Business School.

Common LBS Topics (use these when relevant):
Academic: {academic_topics}
Programs: {program_topics}
Research: {research_topics}
Student Life: {student_life_topics}

Content (first 2000 chars): "{text}"

Extract topics that are:
1. Specific and meaningful (not generic like "information" or "content")
2. Relevant to business education
3. Present in the actual content
4. Appropriate for the page type

Return ONLY the JSON object, no markdown, no explanations.

JSON:"""


class TopicExtractor:
    """
    Extract topics from content using LLM analysis.

    Features:
    - Batch processing with rate limiting
    - Topic normalization and deduplication
    - Semantic similarity checking
    - Relevance score filtering
    """

    def __init__(
        self,
        llm_client: LLMClient,
        min_relevance: float = 0.7,
        max_topics_per_item: int = 5
    ):
        """
        Initialize topic extractor.

        Args:
            llm_client: LLM client for API calls
            min_relevance: Minimum relevance score to keep topics
            max_topics_per_item: Maximum topics to extract per item
        """
        self.llm_client = llm_client
        self.min_relevance = min_relevance
        self.max_topics_per_item = max_topics_per_item

        # Track extracted topics for deduplication
        self.topic_cache: Dict[str, Topic] = {}

        logger.info(f"Initialized TopicExtractor (min_relevance={min_relevance})")

    def normalize_topic(self, topic_name: str) -> str:
        """
        Normalize topic name.

        Args:
            topic_name: Raw topic name

        Returns:
            Normalized topic name
        """
        # Lowercase
        normalized = topic_name.lower()

        # Remove special characters except spaces and hyphens
        normalized = re.sub(r'[^a-z0-9\s-]', '', normalized)

        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)

        # Trim
        normalized = normalized.strip()

        # Title case
        normalized = ' '.join(word.capitalize() for word in normalized.split())

        return normalized

    def is_similar_topic(self, topic1: str, topic2: str) -> bool:
        """
        Check if two topics are similar (basic string matching).

        Args:
            topic1: First topic name
            topic2: Second topic name

        Returns:
            True if topics are similar
        """
        # Exact match
        if topic1 == topic2:
            return True

        # One is substring of other
        if topic1 in topic2 or topic2 in topic1:
            return True

        # Very similar words
        words1 = set(topic1.lower().split())
        words2 = set(topic2.lower().split())

        if len(words1) > 0 and len(words2) > 0:
            overlap = len(words1 & words2) / max(len(words1), len(words2))
            if overlap >= 0.7:  # 70% word overlap
                return True

        return False

    def deduplicate_topics(self, topics: List[Dict]) -> List[Dict]:
        """
        Remove duplicate/similar topics.

        Args:
            topics: List of topic dictionaries

        Returns:
            Deduplicated list
        """
        if not topics:
            return []

        # Sort by relevance (highest first)
        sorted_topics = sorted(topics, key=lambda t: t.get('relevance', 0), reverse=True)

        unique_topics = []
        seen_names = []

        for topic in sorted_topics:
            name = self.normalize_topic(topic['name'])

            # Check against existing topics
            is_duplicate = False
            for seen_name in seen_names:
                if self.is_similar_topic(name, seen_name):
                    is_duplicate = True
                    logger.debug(f"Duplicate topic: {name} (similar to {seen_name})")
                    break

            if not is_duplicate:
                topic['name'] = name  # Use normalized name
                unique_topics.append(topic)
                seen_names.append(name)

        return unique_topics

    async def extract_topics(
        self,
        text: str,
        context: Dict
    ) -> List[Topic]:
        """
        Extract topics from text with context.

        Args:
            text: Content text
            context: Context dict with source_id, source_type, page_type

        Returns:
            List of Topic objects
        """
        if not text or len(text.strip()) < 50:
            logger.debug("Text too short, skipping topic extraction")
            return []

        # Truncate text for prompt (keep first 2000 chars)
        text_preview = text[:2000] if len(text) > 2000 else text

        # Build prompt
        prompt = TOPIC_PROMPT.format(
            page_type=context.get('page_type', 'unknown'),
            text=text_preview.replace('"', '\\"'),
            academic_topics=', '.join(list(TopicTaxonomy.ACADEMIC_TOPICS.keys())[:10]),
            program_topics=', '.join(TopicTaxonomy.PROGRAM_TOPICS),
            research_topics=', '.join(TopicTaxonomy.RESEARCH_TOPICS[:5]),
            student_life_topics=', '.join(TopicTaxonomy.STUDENT_LIFE_TOPICS[:5])
        )

        try:
            # Call LLM
            start_time = datetime.now()

            response = await self.llm_client.client.chat.completions.create(
                model=self.llm_client.model,
                messages=[
                    {"role": "system", "content": "You are a topic extraction expert for business school content. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Low temperature for consistency
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            extraction_time = (datetime.now() - start_time).total_seconds()

            # Parse response
            content = response.choices[0].message.content
            data = json.loads(content)

            # Extract topics
            raw_topics = data.get('topics', [])

            # Deduplicate
            unique_topics = self.deduplicate_topics(raw_topics)

            # Filter by relevance and limit
            filtered_topics = [
                t for t in unique_topics
                if t.get('relevance', 0) >= self.min_relevance
            ][:self.max_topics_per_item]

            # Create Topic objects
            topics = []
            for topic_data in filtered_topics:
                topic_name = topic_data['name']

                # Generate or retrieve topic ID
                if topic_name in self.topic_cache:
                    topic = self.topic_cache[topic_name]
                    topic.frequency += 1
                else:
                    # Infer category
                    category_str = topic_data.get('category', 'general')
                    try:
                        category = TopicCategory(category_str)
                    except ValueError:
                        category = TopicCategory.GENERAL

                    # Create new topic
                    topic = Topic(
                        id=f"topic-{len(self.topic_cache) + 1}",
                        name=topic_name,
                        description=topic_data.get('description'),
                        category=category,
                        discipline=TopicTaxonomy.get_discipline(topic_name),
                        theme=TopicTaxonomy.get_theme(topic_name),
                        frequency=1,
                        importance=topic_data.get('relevance', 0.8),
                        source="llm",
                        extracted_at=datetime.now().isoformat()
                    )

                    self.topic_cache[topic_name] = topic

                topics.append(topic)

            logger.info(f"Extracted {len(topics)} topics from {context.get('source_type')} (filtered from {len(raw_topics)} raw)")

            return topics

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return []

        except Exception as e:
            logger.error(f"Topic extraction error: {e}")
            return []

    async def extract_batch(
        self,
        items: List[Dict],
        batch_size: int = 50
    ) -> List[TopicExtractionResult]:
        """
        Extract topics from multiple items in batches.

        Args:
            items: List of items with 'text' and 'context' fields
            batch_size: Number of items to process concurrently

        Returns:
            List of TopicExtractionResult objects
        """
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            logger.info(f"Processing batch {i // batch_size + 1}/{(len(items) + batch_size - 1) // batch_size} ({len(batch)} items)")

            # Process batch concurrently
            batch_tasks = [
                self.extract_topics(item['text'], item['context'])
                for item in batch
            ]

            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Create results
            for item, topics in zip(batch, batch_results):
                if isinstance(topics, Exception):
                    logger.error(f"Batch item error: {topics}")
                    topics = []

                result = TopicExtractionResult(
                    topics=[{
                        'name': t.name,
                        'relevance': t.importance,
                        'category': t.category.value,
                        'description': t.description
                    } for t in topics],
                    source_id=item['context']['source_id'],
                    source_type=item['context']['source_type'],
                    content_preview=item['text'][:200],
                    extraction_time=0.5  # Placeholder
                )

                results.append(result)

            # Rate limiting delay between batches
            if i + batch_size < len(items):
                await asyncio.sleep(1)

        logger.info(f"Batch extraction complete: {len(results)} items, {len(self.topic_cache)} unique topics")

        return results

    def get_all_topics(self) -> List[Topic]:
        """Get all extracted topics"""
        return list(self.topic_cache.values())

    def get_topic_by_name(self, name: str) -> Optional[Topic]:
        """Get topic by name"""
        normalized = self.normalize_topic(name)
        return self.topic_cache.get(normalized)

    def get_stats(self) -> Dict:
        """Get extraction statistics"""
        return {
            'unique_topics': len(self.topic_cache),
            'total_extractions': sum(t.frequency for t in self.topic_cache.values()),
            'topics_by_category': self._count_by_category(),
            'avg_frequency': sum(t.frequency for t in self.topic_cache.values()) / len(self.topic_cache) if self.topic_cache else 0
        }

    def _count_by_category(self) -> Dict[str, int]:
        """Count topics by category"""
        counts = {}
        for topic in self.topic_cache.values():
            category = topic.category.value
            counts[category] = counts.get(category, 0) + 1
        return counts
