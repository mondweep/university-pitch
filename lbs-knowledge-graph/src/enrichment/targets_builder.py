"""
TARGETS Relationship Builder

Creates Persona nodes and TARGETS relationships from content to personas
with relevance scores and journey stage information.
"""

from typing import List, Dict, Any, Optional
from src.graph.mgraph_wrapper import MGraph

from .persona_models import get_all_personas, PersonaType
from .persona_classifier import PersonaClassification


class TargetsBuilder:
    """
    Builder for TARGETS relationships between content and personas.

    Creates:
    - Persona nodes with metadata
    - TARGETS edges from Page/Section to Persona
    - Multi-target support (content can target multiple personas)
    - Relevance scores and journey stage information
    """

    def __init__(self, graph: MGraph):
        """
        Initialize TARGETS builder.

        Args:
            graph: Memgraph connection
        """
        self.graph = graph
        self.personas_created = 0
        self.relationships_created = 0

    def create_persona_nodes(self) -> int:
        """
        Create Persona nodes in the graph.

        Returns:
            Number of personas created
        """
        print("👥 Creating Persona nodes...")

        personas = get_all_personas()

        for persona in personas:
            query = """
            MERGE (p:Persona {id: $id})
            SET p.name = $name,
                p.type = $type,
                p.slug = $slug,
                p.description = $description,
                p.characteristics = $characteristics,
                p.goals = $goals,
                p.pain_points = $pain_points,
                p.interests = $interests,
                p.priority = $priority,
                p.targeted_content_count = 0
            """

            self.graph.execute(query, {
                "id": persona.id,
                "name": persona.name,
                "type": persona.type.value,
                "slug": persona.slug,
                "description": persona.description,
                "characteristics": persona.characteristics,
                "goals": persona.goals,
                "pain_points": persona.pain_points,
                "interests": persona.interests,
                "priority": persona.priority
            })

            self.personas_created += 1

        print(f"   ✅ Created {self.personas_created} Persona nodes")
        return self.personas_created

    def create_targets_relationships(
        self,
        classifications: List[PersonaClassification]
    ) -> int:
        """
        Create TARGETS relationships from classifications.

        Args:
            classifications: List of PersonaClassification objects

        Returns:
            Number of relationships created
        """
        print("\n🎯 Creating TARGETS relationships...")

        for classification in classifications:
            for persona_data in classification.personas:
                self._create_relationship(
                    content_id=classification.content_id,
                    content_type=classification.content_type,
                    persona_data=persona_data,
                    extracted_by=classification.extracted_by
                )

        print(f"   ✅ Created {self.relationships_created} TARGETS relationships")
        return self.relationships_created

    def _create_relationship(
        self,
        content_id: str,
        content_type: str,
        persona_data: Dict[str, Any],
        extracted_by: str
    ):
        """Create a single TARGETS relationship."""
        # Determine content node label
        content_label = "Page" if content_type == "page" else "Section"

        query = f"""
        MATCH (c:{content_label} {{id: $content_id}})
        MATCH (p:Persona {{id: $persona_id}})
        MERGE (c)-[r:TARGETS]->(p)
        SET r.relationship_type = 'TARGETS',
            r.persona_id = $persona_id,
            r.relevance = $relevance,
            r.is_primary = $is_primary,
            r.journey_stage = $journey_stage,
            r.signals = $signals,
            r.intent = $intent,
            r.confidence = $confidence,
            r.extracted_by = $extracted_by
        """

        try:
            self.graph.execute(query, {
                "content_id": content_id,
                "persona_id": persona_data["persona_id"],
                "relevance": persona_data["relevance"],
                "is_primary": persona_data.get("is_primary", False),
                "journey_stage": persona_data["journey_stage"],
                "signals": persona_data.get("signals", []),
                "intent": persona_data.get("intent", ""),
                "confidence": persona_data.get("confidence", 0.9),
                "extracted_by": extracted_by
            })

            self.relationships_created += 1

        except Exception as e:
            print(f"⚠️  Error creating TARGETS relationship: {e}")

    def update_persona_statistics(self) -> Dict[str, int]:
        """
        Update targeted_content_count for all personas.

        Returns:
            Dictionary of persona_id -> count
        """
        print("\n📊 Updating persona statistics...")

        query = """
        MATCH (p:Persona)<-[r:TARGETS]-(content)
        WITH p, count(content) AS content_count
        SET p.targeted_content_count = content_count
        RETURN p.id AS persona_id, p.name AS name, content_count
        """

        results = self.graph.execute_and_fetch(query)
        stats = {}

        for row in results:
            persona_id = row["persona_id"]
            name = row["name"]
            count = row["content_count"]
            stats[persona_id] = count
            print(f"   {name}: {count} targeted items")

        return stats

    def get_multi_target_content(self) -> List[Dict[str, Any]]:
        """
        Get content that targets multiple personas.

        Returns:
            List of content items with their target personas
        """
        query = """
        MATCH (content)-[r:TARGETS]->(p:Persona)
        WITH content, count(p) AS persona_count, collect({
            persona_name: p.name,
            relevance: r.relevance,
            is_primary: r.is_primary
        }) AS personas
        WHERE persona_count > 1
        RETURN
            labels(content)[0] AS content_type,
            content.id AS content_id,
            content.title AS title,
            persona_count,
            personas
        ORDER BY persona_count DESC
        LIMIT 50
        """

        results = self.graph.execute_and_fetch(query)
        return [dict(row) for row in results]

    def get_persona_overlap_matrix(self) -> Dict[str, Dict[str, int]]:
        """
        Calculate persona overlap matrix (how often personas co-target content).

        Returns:
            Matrix of persona_id -> persona_id -> count
        """
        query = """
        MATCH (content)-[:TARGETS]->(p1:Persona)
        MATCH (content)-[:TARGETS]->(p2:Persona)
        WHERE p1.id < p2.id
        RETURN p1.name AS persona1, p2.name AS persona2, count(content) AS overlap_count
        ORDER BY overlap_count DESC
        """

        results = self.graph.execute_and_fetch(query)

        matrix = {}
        for row in results:
            p1 = row["persona1"]
            p2 = row["persona2"]
            count = row["overlap_count"]

            if p1 not in matrix:
                matrix[p1] = {}
            matrix[p1][p2] = count

        return matrix

    def get_journey_stage_distribution(self) -> Dict[str, Dict[str, int]]:
        """
        Get distribution of journey stages by persona.

        Returns:
            Dictionary of persona -> journey_stage -> count
        """
        query = """
        MATCH (content)-[r:TARGETS]->(p:Persona)
        RETURN
            p.name AS persona_name,
            r.journey_stage AS journey_stage,
            count(*) AS count
        ORDER BY persona_name, count DESC
        """

        results = self.graph.execute_and_fetch(query)

        distribution = {}
        for row in results:
            persona = row["persona_name"]
            stage = row["journey_stage"]
            count = row["count"]

            if persona not in distribution:
                distribution[persona] = {}
            distribution[persona][stage] = count

        return distribution

    def validate_relationships(self) -> Dict[str, Any]:
        """
        Validate TARGETS relationships.

        Returns:
            Validation report
        """
        print("\n🔍 Validating TARGETS relationships...")

        # Check for orphaned personas
        orphaned_query = """
        MATCH (p:Persona)
        WHERE NOT (p)<-[:TARGETS]-()
        RETURN count(p) AS orphaned_count, collect(p.name) AS orphaned_personas
        """

        orphaned_result = list(self.graph.execute_and_fetch(orphaned_query))[0]

        # Check relevance score distribution
        relevance_query = """
        MATCH ()-[r:TARGETS]->()
        RETURN
            min(r.relevance) AS min_relevance,
            max(r.relevance) AS max_relevance,
            avg(r.relevance) AS avg_relevance,
            count(r) AS total_relationships
        """

        relevance_result = list(self.graph.execute_and_fetch(relevance_query))[0]

        # Check primary persona coverage
        primary_query = """
        MATCH (content)-[r:TARGETS {is_primary: true}]->()
        RETURN count(DISTINCT content) AS content_with_primary
        """

        primary_result = list(self.graph.execute_and_fetch(primary_query))[0]

        report = {
            "orphaned_personas": {
                "count": orphaned_result["orphaned_count"],
                "personas": orphaned_result.get("orphaned_personas", [])
            },
            "relevance_scores": {
                "min": round(relevance_result["min_relevance"], 2),
                "max": round(relevance_result["max_relevance"], 2),
                "avg": round(relevance_result["avg_relevance"], 2)
            },
            "total_relationships": relevance_result["total_relationships"],
            "content_with_primary_persona": primary_result["content_with_primary"]
        }

        print(f"   Total TARGETS relationships: {report['total_relationships']}")
        print(f"   Orphaned personas: {report['orphaned_personas']['count']}")
        print(f"   Avg relevance score: {report['relevance_scores']['avg']}")
        print(f"   Content with primary persona: {report['content_with_primary_persona']}")

        return report
