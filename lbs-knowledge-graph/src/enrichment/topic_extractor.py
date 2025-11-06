"""
Topic Extractor for Knowledge Graph

Extracts 5-10 topics per page using LLM and creates HAS_TOPIC relationships.
"""

import asyncio
import re
from typing import List, Dict, Optional, Set
from datetime import datetime
import uuid

from .llm_client import LLMClient
from .topic_models import (
    Topic, TopicCategory, TopicTaxonomy, TopicExtractionResult,
    BusinessDiscipline, CrossCuttingTheme
)
from mgraph import MGraph


# Topic extraction prompt
TOPIC_EXTRACTION_PROMPT = """Extract 5-10 main topics from this page content. Focus on academic subjects, programme types, research areas, and key themes.

Page Title: {title}
Page Type: {page_type}

Page Content:
{content}

Return ONLY valid JSON with no additional text:
[
  {{"topic": "MBA Programme", "relevance": 0.95, "category": "academic"}},
  {{"topic": "Leadership Development", "relevance": 0.85, "category": "academic"}},
  {{"topic": "Career Services", "relevance": 0.80, "category": "student_life"}},
  ...
]

Focus on:
- Academic programmes and disciplines (MBA, Masters, Executive Education, PhD)
- Research areas and themes (Finance, Marketing, Strategy, Economics)
- Skills and competencies (Leadership, Analytics, Communication)
- Business sectors and industries (Technology, Finance, Healthcare)
- Career paths and roles (Executive, Consultant, Entrepreneur)
- Cross-cutting themes (Sustainability, Digital Transformation, Diversity)

Categories: academic, research, student_life, business, alumni, events, admissions, career, faculty, general

Return ONLY the JSON array, no markdown, no explanations."""


class TopicExtractor:
    """
    Extract topics from pages using LLM analysis.

    Extracts 5-10 topics per page, normalizes topic names,
    and filters low-relevance topics.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        graph: MGraph,
        relevance_threshold: float = 0.7,
        max_topics_per_page: int = 10,
        min_topics_per_page: int = 5
    ):
        """
        Initialize topic extractor.

        Args:
            llm_client: LLM client for topic extraction
            graph: MGraph instance
            relevance_threshold: Minimum relevance score to keep topic (0-1)
            max_topics_per_page: Maximum topics per page
            min_topics_per_page: Minimum topics per page
        """
        self.llm_client = llm_client
        self.graph = graph
        self.relevance_threshold = relevance_threshold
        self.max_topics_per_page = max_topics_per_page
        self.min_topics_per_page = min_topics_per_page

        # Topic cache for deduplication
        self.topic_cache: Dict[str, Topic] = {}
        self.topic_id_map: Dict[str, str] = {}  # normalized_name -> topic_id

    async def extract_topics_from_pages(self, limit: int = 10) -> List[TopicExtractionResult]:
        """
        Extract topics from pages in the graph.

        Args:
            limit: Maximum number of pages to process

        Returns:
            List of TopicExtractionResult objects
        """
        # Get pages from graph
        pages = self.graph.search_nodes(node_type="Page", limit=limit)

        if not pages:
            print("⚠️  No pages found in graph")
            return []

        print(f"📄 Found {len(pages)} pages to process")

        results = []
        for i, page in enumerate(pages):
            print(f"\n[{i+1}/{len(pages)}] Processing page: {page.get('title', 'Untitled')[:50]}...")

            try:
                result = await self.extract_topics_from_page(page)
                results.append(result)

                # Show extracted topics
                print(f"  ✅ Extracted {len(result.topics)} topics")
                for topic_data in result.topics[:3]:  # Show first 3
                    print(f"     • {topic_data['name']} (relevance: {topic_data['relevance']:.2f})")

            except Exception as e:
                print(f"  ❌ Error extracting topics: {e}")
                continue

        return results

    async def extract_topics_from_page(self, page: Dict) -> TopicExtractionResult:
        """
        Extract topics from a single page.

        Args:
            page: Page node dictionary

        Returns:
            TopicExtractionResult
        """
        start_time = datetime.now()

        # Prepare page content
        content = self.prepare_page_content(page)

        # Create prompt
        prompt = TOPIC_EXTRACTION_PROMPT.format(
            title=page.get('title', 'Untitled'),
            page_type=page.get('type', 'other'),
            content=content
        )

        # Call LLM (reuse sentiment analysis client with custom prompt)
        import json
        from openai import AsyncOpenAI

        api_key = self.llm_client.api_key
        client = AsyncOpenAI(api_key=api_key, timeout=30)

        try:
            response = await client.chat.completions.create(
                model="gpt-4-turbo",  # Use GPT-4-turbo for better accuracy
                messages=[
                    {"role": "system", "content": "You are a topic extraction expert. Return ONLY valid JSON arrays."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            # Track usage
            self.llm_client.api_calls += 1
            usage = response.usage
            self.llm_client.total_tokens += usage.total_tokens

            # Calculate cost (GPT-4-turbo: $10/1M input, $30/1M output)
            input_cost = (usage.prompt_tokens / 1_000_000) * 10.00
            output_cost = (usage.completion_tokens / 1_000_000) * 30.00
            self.llm_client.total_cost += input_cost + output_cost

            # Parse response
            content_text = response.choices[0].message.content

            # Extract JSON array from response
            data = json.loads(content_text)

            # Handle both array and object with topics key
            if isinstance(data, dict) and 'topics' in data:
                topic_list = data['topics']
            elif isinstance(data, list):
                topic_list = data
            else:
                topic_list = []

            # Parse topics
            topics = self.parse_topic_results(topic_list, page)

            # Filter by relevance
            topics = [t for t in topics if t['relevance'] >= self.relevance_threshold]

            # Limit to max topics
            topics = sorted(topics, key=lambda x: x['relevance'], reverse=True)[:self.max_topics_per_page]

            extraction_time = (datetime.now() - start_time).total_seconds()

            return TopicExtractionResult(
                topics=topics,
                source_id=page['id'],
                source_type='Page',
                content_preview=content[:200],
                total_tokens=usage.total_tokens,
                extraction_time=extraction_time
            )

        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON parse error: {e}")
            # Return empty result
            return TopicExtractionResult(
                topics=[],
                source_id=page['id'],
                source_type='Page',
                content_preview=content[:200]
            )

        except Exception as e:
            print(f"  ⚠️  Extraction error: {e}")
            raise

    def prepare_page_content(self, page: Dict) -> str:
        """
        Prepare page content for topic extraction.

        Extracts title, description, and key content sections.

        Args:
            page: Page node dictionary

        Returns:
            Prepared content string (max 1000 chars)
        """
        parts = []

        # Title
        if page.get('title'):
            parts.append(page['title'])

        # Description
        if page.get('description'):
            parts.append(page['description'])

        # OG Description
        if page.get('og_description'):
            parts.append(page['og_description'])

        # Keywords
        if page.get('keywords'):
            keywords = page['keywords']
            if isinstance(keywords, list):
                parts.append(' '.join(keywords))
            else:
                parts.append(str(keywords))

        # Type and category provide context
        if page.get('type'):
            parts.append(f"Page type: {page['type']}")

        if page.get('category'):
            parts.append(f"Category: {page['category']}")

        # Combine and truncate
        content = '\n'.join(parts)

        # Truncate to 1000 chars for efficiency
        if len(content) > 1000:
            content = content[:1000]

        return content

    def parse_topic_results(self, results: List[Dict], page: Dict) -> List[Dict]:
        """
        Parse LLM results into Topic entities.

        Args:
            results: Raw LLM results
            page: Source page

        Returns:
            List of topic dictionaries with normalized names
        """
        topics = []
        seen_names: Set[str] = set()

        for item in results:
            if not isinstance(item, dict):
                continue

            # Extract topic name
            topic_name = item.get('topic', '').strip()
            if not topic_name:
                continue

            # Normalize name
            normalized_name = self.normalize_topic_name(topic_name)

            # Skip duplicates
            if normalized_name in seen_names:
                continue
            seen_names.add(normalized_name)

            # Get or create topic ID
            if normalized_name not in self.topic_id_map:
                self.topic_id_map[normalized_name] = str(uuid.uuid4())

            topic_id = self.topic_id_map[normalized_name]

            # Infer category
            category_str = item.get('category', 'general')
            category = self.infer_category(normalized_name, category_str)

            # Get relevance score
            relevance = float(item.get('relevance', 0.8))

            # Create topic dictionary
            topic_dict = {
                'id': topic_id,
                'name': normalized_name,
                'original_name': topic_name,
                'category': category.value,
                'relevance': relevance,
                'confidence': 0.85,  # Default confidence
                'source': 'llm',
                'model': 'gpt-4-turbo',
                'page_id': page['id']
            }

            # Add discipline/theme if applicable
            discipline = TopicTaxonomy.get_discipline(normalized_name)
            if discipline:
                topic_dict['discipline'] = discipline.value

            theme = TopicTaxonomy.get_theme(normalized_name)
            if theme:
                topic_dict['theme'] = theme.value

            topics.append(topic_dict)

        return topics

    def normalize_topic_name(self, topic: str) -> str:
        """
        Normalize topic names for consistency.

        Rules:
        - Convert to title case
        - Remove extra whitespace
        - Standardize common terms
        - Use singular form where appropriate

        Args:
            topic: Raw topic name

        Returns:
            Normalized topic name
        """
        # Basic cleanup
        topic = topic.strip()
        topic = re.sub(r'\s+', ' ', topic)  # Collapse whitespace

        # Title case
        topic = topic.title()

        # Standardize common abbreviations
        replacements = {
            'Mba': 'MBA',
            'Emba': 'EMBA',
            'Phd': 'PhD',
            'Esg': 'ESG',
            'Ai': 'AI',
            'It': 'IT',
            'Hr': 'HR',
            'Ceo': 'CEO',
            'Cfo': 'CFO',
            'Cto': 'CTO'
        }

        for old, new in replacements.items():
            topic = topic.replace(old, new)

        # Remove common suffixes for singular form
        # But keep for specific terms
        if not any(keep in topic for keep in ['Services', 'Studies', 'Analytics', 'Economics']):
            if topic.endswith('ies'):
                topic = topic[:-3] + 'y'
            elif topic.endswith('s') and not topic.endswith('ss'):
                topic = topic[:-1]

        return topic

    def infer_category(self, topic_name: str, category_hint: str) -> TopicCategory:
        """
        Infer topic category from name and hint.

        Args:
            topic_name: Normalized topic name
            category_hint: Category hint from LLM

        Returns:
            TopicCategory enum
        """
        # First try taxonomy-based classification
        category = TopicTaxonomy.get_category_for_topic(topic_name)
        if category != TopicCategory.GENERAL:
            return category

        # Use LLM hint
        category_map = {
            'academic': TopicCategory.ACADEMIC,
            'research': TopicCategory.RESEARCH,
            'student_life': TopicCategory.STUDENT_LIFE,
            'business': TopicCategory.BUSINESS,
            'alumni': TopicCategory.ALUMNI,
            'events': TopicCategory.EVENTS,
            'admissions': TopicCategory.ADMISSIONS,
            'career': TopicCategory.CAREER,
            'faculty': TopicCategory.FACULTY
        }

        return category_map.get(category_hint.lower(), TopicCategory.GENERAL)

    def deduplicate_topics(self, topics: List[Dict]) -> List[Dict]:
        """
        Remove duplicate or very similar topics.

        Uses normalized names for exact duplicates.
        Could be extended with similarity matching.

        Args:
            topics: List of topic dictionaries

        Returns:
            Deduplicated list
        """
        seen: Set[str] = set()
        unique_topics = []

        # Sort by relevance (keep highest relevance for duplicates)
        sorted_topics = sorted(topics, key=lambda x: x['relevance'], reverse=True)

        for topic in sorted_topics:
            name = topic['name']
            if name not in seen:
                seen.add(name)
                unique_topics.append(topic)

        return unique_topics

    def get_stats(self) -> Dict:
        """Get extraction statistics"""
        return {
            'unique_topics': len(self.topic_id_map),
            'topics_in_cache': len(self.topic_cache),
            'llm_stats': self.llm_client.get_stats()
        }
