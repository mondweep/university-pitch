"""
Named Entity Recognition (NER) Extractor

Extracts named entities (people, organizations, locations, events) from content
using LLM-based extraction with high accuracy.
"""

import os
import json
import asyncio
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from openai import AsyncOpenAI

from .entity_models import Entity, EntityType, EntityMention, EntityRelationship, NERExtractionResult


# NER extraction prompt for GPT-4-turbo
NER_PROMPT = """Extract all named entities from this content. Identify people, organizations, locations, and events with high precision.

Content:
{content}

Return ONLY valid JSON with no markdown or additional text:
{{
  "entities": [
    {{
      "text": "Professor Jane Smith",
      "type": "PERSON",
      "metadata": {{
        "role": "Professor",
        "department": "Finance",
        "affiliation": "London Business School"
      }},
      "context": "Professor Jane Smith leads the Finance department...",
      "confidence": 0.95,
      "position": 0
    }},
    {{
      "text": "London Business School",
      "type": "ORGANIZATION",
      "metadata": {{
        "type": "Business School",
        "location": "London"
      }},
      "context": "at London Business School...",
      "confidence": 0.98,
      "position": 50
    }}
  ]
}}

Entity types:
- PERSON: Faculty, staff, alumni, students, guest speakers (include role, title, department)
- ORGANIZATION: Companies, institutions, research centers, departments (include type, industry)
- LOCATION: Cities, countries, campuses, buildings (include type: city, country, etc.)
- EVENT: Conferences, seminars, programmes, initiatives (include date if available)

Rules:
- Extract only clearly identifiable entities
- Include role/title/affiliation for people when available
- Include organization type and industry when clear
- Provide surrounding context (20-50 words)
- Position is character index in original content
- Confidence: 0.0-1.0 based on clarity of entity
- Return ONLY the JSON object

JSON:"""


class NERExtractor:
    """
    Extracts named entities from content using GPT-4-turbo.

    Uses high-accuracy model for precise entity extraction with
    classification, metadata extraction, and entity resolution.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo",
        batch_size: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize NER extractor.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4-turbo for high accuracy)
            batch_size: Number of items to process in parallel
            max_retries: Maximum number of retries on failure
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")

        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries

        self.client = AsyncOpenAI(api_key=self.api_key, timeout=60)

        # Cost tracking
        self.total_tokens = 0
        self.total_cost = 0.0
        self.api_calls = 0

        # Model pricing (per 1M tokens)
        self.pricing = {
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-4o": {"input": 2.50, "output": 10.00}
        }

        # Entity resolution cache (map variations to canonical names)
        self.entity_cache: Dict[str, str] = {}

    async def extract_entities_from_content(
        self,
        content_id: str,
        content: str
    ) -> NERExtractionResult:
        """
        Extract all entities from a single content item.

        Args:
            content_id: ID of the content item
            content: Text content to analyze

        Returns:
            NERExtractionResult with entities, mentions, and relationships
        """
        start_time = datetime.now()

        # Truncate very long content (max 3000 chars for NER)
        if len(content) > 3000:
            content = content[:3000]

        prompt = NER_PROMPT.format(content=content.replace('"', '\\"'))

        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a Named Entity Recognition expert. Return ONLY valid JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # Low temperature for consistency
                    max_tokens=1500,  # NER needs more tokens for entity lists
                    response_format={"type": "json_object"}
                )

                # Track usage
                self.api_calls += 1
                usage = response.usage
                self.total_tokens += usage.total_tokens

                # Calculate cost
                if self.model in self.pricing:
                    input_cost = (usage.prompt_tokens / 1_000_000) * self.pricing[self.model]["input"]
                    output_cost = (usage.completion_tokens / 1_000_000) * self.pricing[self.model]["output"]
                    cost = input_cost + output_cost
                    self.total_cost += cost
                else:
                    cost = 0.0

                # Parse response
                content_json = response.choices[0].message.content
                data = json.loads(content_json)

                # Process entities
                entities = []
                mentions = []

                for entity_data in data.get("entities", []):
                    entity_text = entity_data["text"]
                    entity_type = EntityType(entity_data["type"])

                    # Normalize entity name
                    canonical_name = self.normalize_entity_name(entity_text, entity_type)

                    # Create entity ID
                    entity_id = str(uuid.uuid4())

                    # Create entity
                    entity = Entity(
                        id=entity_id,
                        name=entity_text,
                        entity_type=entity_type,
                        canonical_name=canonical_name,
                        aliases=[entity_text],
                        metadata=entity_data.get("metadata", {}),
                        mention_count=1,
                        first_mentioned=datetime.now(),
                        prominence=self._calculate_prominence(
                            entity_data.get("position", 0),
                            len(content)
                        ),
                        confidence=entity_data.get("confidence", 0.9)
                    )
                    entities.append(entity)

                    # Create mention
                    mention = EntityMention(
                        entity_id=entity_id,
                        content_id=content_id,
                        entity_text=entity_text,
                        context=entity_data.get("context", "")[:200],
                        prominence=self._get_prominence_level(entity.prominence),
                        confidence=entity.confidence,
                        position=entity_data.get("position", 0),
                        extracted_by=self.model
                    )
                    mentions.append(mention)

                # Extract relationships between entities
                relationships = self._extract_relationships(entities, content)

                # Calculate extraction time
                extraction_time = (datetime.now() - start_time).total_seconds()

                return NERExtractionResult(
                    content_id=content_id,
                    entities=entities,
                    mentions=mentions,
                    relationships=relationships,
                    extraction_time=extraction_time,
                    cost=cost,
                    model_used=self.model
                )

            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parse error for content {content_id} (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    return NERExtractionResult(content_id=content_id)
                await asyncio.sleep(1 * (attempt + 1))

            except Exception as e:
                print(f"⚠️  API error for content {content_id} (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    return NERExtractionResult(content_id=content_id)
                await asyncio.sleep(2 * (attempt + 1))

        return NERExtractionResult(content_id=content_id)

    def normalize_entity_name(self, name: str, entity_type: EntityType) -> str:
        """
        Normalize entity name to canonical form.

        Examples:
        - "Dr. Jane Smith" -> "Jane Smith"
        - "Professor Smith" -> "Smith"
        - "LBS" -> "London Business School"
        """
        # Remove titles for people
        if entity_type == EntityType.PERSON:
            titles = ["Dr.", "Prof.", "Professor", "Mr.", "Ms.", "Mrs.", "Miss"]
            for title in titles:
                if name.startswith(title):
                    name = name[len(title):].strip()

        # Check entity cache for known variations
        if name in self.entity_cache:
            return self.entity_cache[name]

        return name

    def _calculate_prominence(self, position: int, content_length: int) -> float:
        """
        Calculate entity prominence based on position in content.

        Entities mentioned earlier are more prominent (title, first paragraph).
        """
        if content_length == 0:
            return 0.5

        # Normalize position to 0-1
        normalized_position = position / content_length

        # Higher prominence for earlier mentions
        # Position 0 (start) = 1.0, Position 1.0 (end) = 0.3
        prominence = 1.0 - (normalized_position * 0.7)

        return max(0.3, min(1.0, prominence))

    def _get_prominence_level(self, prominence: float) -> str:
        """Convert numeric prominence to level"""
        if prominence >= 0.7:
            return "high"
        elif prominence >= 0.4:
            return "medium"
        else:
            return "low"

    def _extract_relationships(
        self,
        entities: List[Entity],
        content: str
    ) -> List[EntityRelationship]:
        """
        Extract relationships between entities in the same content.

        Simple heuristic-based relationship extraction:
        - Person mentioned with Organization -> AFFILIATED_WITH
        - Organization mentioned with Location -> LOCATED_AT
        - Multiple people mentioned together -> WORKS_WITH
        """
        relationships = []

        # Find person-organization relationships
        people = [e for e in entities if e.entity_type == EntityType.PERSON]
        orgs = [e for e in entities if e.entity_type == EntityType.ORGANIZATION]
        locations = [e for e in entities if e.entity_type == EntityType.LOCATION]

        # AFFILIATED_WITH (person-organization)
        for person in people:
            # Check if person's metadata has affiliation
            if "affiliation" in person.metadata:
                for org in orgs:
                    if org.name in person.metadata["affiliation"]:
                        relationships.append(EntityRelationship(
                            from_entity_id=person.id,
                            to_entity_id=org.id,
                            relationship_type="AFFILIATED_WITH",
                            confidence=0.9,
                            evidence=f"{person.name} affiliated with {org.name}"
                        ))

        # LOCATED_AT (organization-location)
        for org in orgs:
            if "location" in org.metadata:
                for location in locations:
                    if location.name in org.metadata["location"]:
                        relationships.append(EntityRelationship(
                            from_entity_id=org.id,
                            to_entity_id=location.id,
                            relationship_type="LOCATED_AT",
                            confidence=0.85,
                            evidence=f"{org.name} located in {location.name}"
                        ))

        # WORKS_WITH (person-person, simple heuristic)
        for i, person1 in enumerate(people):
            for person2 in people[i+1:]:
                # If both from same organization, likely work together
                if person1.metadata.get("affiliation") == person2.metadata.get("affiliation"):
                    relationships.append(EntityRelationship(
                        from_entity_id=person1.id,
                        to_entity_id=person2.id,
                        relationship_type="WORKS_WITH",
                        confidence=0.7,
                        evidence=f"{person1.name} and {person2.name} at same organization"
                    ))

        return relationships

    async def extract_batch(
        self,
        content_items: List[Dict[str, str]]
    ) -> List[NERExtractionResult]:
        """
        Extract entities from multiple content items in parallel batches.

        Args:
            content_items: List of dicts with 'id' and 'content' keys

        Returns:
            List of NERExtractionResult objects
        """
        results = []

        for i in range(0, len(content_items), self.batch_size):
            batch = content_items[i:i + self.batch_size]

            print(f"🔄 Processing batch {i//self.batch_size + 1}/{(len(content_items) + self.batch_size - 1)//self.batch_size}...")

            batch_results = await asyncio.gather(
                *[
                    self.extract_entities_from_content(item["id"], item["content"])
                    for item in batch
                ],
                return_exceptions=True
            )

            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"⚠️  Batch error: {result}")
                    results.append(NERExtractionResult(content_id="unknown"))
                else:
                    results.append(result)

        return results

    def resolve_entity_mentions(
        self,
        all_entities: List[Entity]
    ) -> Dict[str, List[str]]:
        """
        Resolve entity mentions by finding variations of the same entity.

        Returns:
            Dictionary mapping canonical names to list of variations
        """
        canonical_map: Dict[str, List[str]] = {}

        for entity in all_entities:
            canonical = entity.canonical_name
            if canonical not in canonical_map:
                canonical_map[canonical] = []

            # Add all variations
            if entity.name not in canonical_map[canonical]:
                canonical_map[canonical].append(entity.name)

            for alias in entity.aliases:
                if alias not in canonical_map[canonical]:
                    canonical_map[canonical].append(alias)

        return canonical_map

    def get_stats(self) -> dict:
        """Get extraction statistics"""
        return {
            "api_calls": self.api_calls,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 2),
            "avg_tokens_per_call": round(self.total_tokens / self.api_calls, 1) if self.api_calls > 0 else 0,
            "model": self.model
        }
