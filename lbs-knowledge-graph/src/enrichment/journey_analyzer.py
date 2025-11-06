"""
Journey Analyzer - Analyzes Persona Content Pathways

Analyzes typical content journeys for each persona:
- Identifies entry points (typical first pages)
- Identifies conversion points (key decision pages)
- Maps pages to journey stages
- Calculates journey completion rates
- Identifies typical paths through content
"""

import logging
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, Counter
import numpy as np

from src.graph.mgraph_wrapper import MGraph
from src.enrichment.journey_models import (
    Journey, JourneyStage, JourneyPath, EntryPoint, ConversionPoint,
    JourneyStageInfo, PERSONAS, get_persona_name
)


logger = logging.getLogger(__name__)


class JourneyAnalyzer:
    """Analyzes persona journeys through content"""

    def __init__(self, graph: MGraph):
        """
        Initialize journey analyzer

        Args:
            graph: MGraph instance with TARGETS relationships
        """
        self.graph = graph
        self.personas = list(PERSONAS.keys())

    def analyze_persona_journey(self, persona_id: str) -> Journey:
        """
        Analyze complete journey for a persona

        Args:
            persona_id: Persona identifier

        Returns:
            Journey object with complete analysis
        """
        logger.info(f"Analyzing journey for persona: {persona_id}")

        # Get all pages targeted at this persona
        targeted_pages = self._get_targeted_pages(persona_id)
        logger.info(f"  Found {len(targeted_pages)} targeted pages")

        if not targeted_pages:
            logger.warning(f"  No targeted pages found for {persona_id}")
            return self._create_empty_journey(persona_id)

        # Analyze entry points
        entry_points = self.find_entry_points(persona_id, targeted_pages)
        logger.info(f"  Identified {len(entry_points)} entry points")

        # Analyze conversion points
        conversion_points = self.find_conversion_points(persona_id, targeted_pages)
        logger.info(f"  Identified {len(conversion_points)} conversion points")

        # Map pages to journey stages
        stage_mapping = self.map_journey_stages(persona_id, targeted_pages)
        stages = self._build_stage_info(stage_mapping)
        logger.info(f"  Mapped pages to {len(stages)} journey stages")

        # Identify typical paths
        typical_paths = self.identify_typical_paths(persona_id, targeted_pages, stage_mapping)
        logger.info(f"  Identified {len(typical_paths)} typical paths")

        # Calculate journey metrics
        avg_path_length = np.mean([p.length for p in typical_paths]) if typical_paths else 0.0
        overall_completion = np.mean([p.completion_rate for p in typical_paths]) if typical_paths else 0.0

        journey = Journey(
            journey_id=f"journey-{persona_id}",
            persona_id=persona_id,
            persona_name=get_persona_name(persona_id),
            entry_points=entry_points,
            conversion_points=conversion_points,
            stages=stages,
            typical_paths=typical_paths,
            avg_path_length=avg_path_length,
            overall_completion_rate=overall_completion,
            page_count=len(targeted_pages),
            path_count=len(typical_paths)
        )

        return journey

    def _get_targeted_pages(self, persona_id: str) -> List[str]:
        """Get all pages with TARGETS relationship to this persona"""
        query = f"""
        MATCH (page:Page)-[t:TARGETS]->(persona:Persona {{id: '{persona_id}'}})
        RETURN page.id as page_id
        ORDER BY page.id
        """
        results = self.graph.execute_query(query)
        return [r['page_id'] for r in results]

    def find_entry_points(self, persona_id: str, targeted_pages: Optional[List[str]] = None) -> List[EntryPoint]:
        """
        Find typical entry points for a persona

        Entry points are identified by:
        1. Low URL depth (closer to homepage)
        2. High importance score
        3. Broad/introductory content
        4. Few incoming links (external entry likely)

        Args:
            persona_id: Persona identifier
            targeted_pages: List of page IDs (optional, will query if not provided)

        Returns:
            List of EntryPoint objects
        """
        if targeted_pages is None:
            targeted_pages = self._get_targeted_pages(persona_id)

        entry_points = []
        persona_interests = PERSONAS.get(persona_id, {}).get("interests", [])

        for page_id in targeted_pages:
            # Get page properties
            page_data = self._get_page_data(page_id)
            if not page_data:
                continue

            # Calculate entry score
            url_depth = page_data.get('url', '').count('/') - 2  # Subtract base domain
            importance = page_data.get('importance', 0.5)
            page_type = page_data.get('type', 'other')

            # Entry score: lower depth + higher importance = higher score
            entry_score = importance / max(url_depth, 1)

            # Boost score if page type matches persona interests
            if any(interest in page_type.lower() for interest in persona_interests):
                entry_score *= 1.5

            # Determine stage (entry points typically in AWARENESS or CONSIDERATION)
            stage = JourneyStage.AWARENESS if url_depth <= 2 else JourneyStage.CONSIDERATION

            entry_points.append({
                'page_id': page_id,
                'page_url': page_data.get('url', ''),
                'page_title': page_data.get('title', page_id),
                'entry_score': entry_score,
                'stage': stage
            })

        # Sort by entry score and take top N
        entry_points.sort(key=lambda x: x['entry_score'], reverse=True)
        top_entries = entry_points[:3]  # Top 3 entry points

        # Convert to EntryPoint objects with normalized entry rates
        total_score = sum(e['entry_score'] for e in top_entries) or 1.0
        result = []

        for ep in top_entries:
            result.append(EntryPoint(
                page_id=ep['page_id'],
                page_url=ep['page_url'],
                page_title=ep['page_title'],
                entry_rate=ep['entry_score'] / total_score,
                stage=ep['stage'],
                traffic_sources=self._estimate_traffic_sources(ep['page_url'])
            ))

        return result

    def find_conversion_points(self, persona_id: str, targeted_pages: Optional[List[str]] = None) -> List[ConversionPoint]:
        """
        Find key conversion points for a persona

        Conversion points are identified by:
        1. Action-oriented page types (admissions, contact, apply)
        2. High outgoing link count (end of journey)
        3. Decision-stage content
        4. Call-to-action presence

        Args:
            persona_id: Persona identifier
            targeted_pages: List of page IDs (optional)

        Returns:
            List of ConversionPoint objects
        """
        if targeted_pages is None:
            targeted_pages = self._get_targeted_pages(persona_id)

        conversion_points = []
        action_keywords = ['admission', 'apply', 'contact', 'register', 'enquire', 'enrol']

        for page_id in targeted_pages:
            page_data = self._get_page_data(page_id)
            if not page_data:
                continue

            url = page_data.get('url', '').lower()
            page_type = page_data.get('type', 'other').lower()
            title = page_data.get('title', '').lower()

            # Calculate conversion score
            conversion_score = 0.0

            # Check for action keywords in URL or title
            if any(keyword in url or keyword in title for keyword in action_keywords):
                conversion_score += 0.5

            # Check page type
            if page_type in ['admissions', 'contact', 'application']:
                conversion_score += 0.3

            # Pages with fewer incoming links are often conversion endpoints
            incoming_count = self._count_incoming_links(page_id)
            if incoming_count > 2:
                conversion_score += 0.2

            if conversion_score > 0.3:  # Threshold for conversion pages
                conversion_points.append({
                    'page_id': page_id,
                    'page_url': page_data.get('url', ''),
                    'page_title': page_data.get('title', page_id),
                    'conversion_score': conversion_score
                })

        # Sort by conversion score and take top 2
        conversion_points.sort(key=lambda x: x['conversion_score'], reverse=True)
        top_conversions = conversion_points[:2]

        # Convert to ConversionPoint objects
        result = []
        for cp in top_conversions:
            # Simulate conversion rate (would be from analytics in production)
            conversion_rate = min(cp['conversion_score'], 0.8)

            result.append(ConversionPoint(
                page_id=cp['page_id'],
                page_url=cp['page_url'],
                page_title=cp['page_title'],
                conversion_rate=conversion_rate,
                stage=JourneyStage.ACTION,
                conversion_actions=self._identify_conversion_actions(cp['page_url'])
            ))

        return result

    def map_journey_stages(self, persona_id: str, targeted_pages: Optional[List[str]] = None) -> Dict[str, JourneyStage]:
        """
        Map pages to journey stages

        Stage mapping based on:
        1. URL depth (shallow = awareness, deep = decision)
        2. Page type (programme = consideration, admission = action)
        3. Content focus (broad vs specific)
        4. Position in link graph

        Args:
            persona_id: Persona identifier
            targeted_pages: List of page IDs (optional)

        Returns:
            Dict mapping page_id to JourneyStage
        """
        if targeted_pages is None:
            targeted_pages = self._get_targeted_pages(persona_id)

        stage_mapping = {}

        for page_id in targeted_pages:
            page_data = self._get_page_data(page_id)
            if not page_data:
                continue

            url = page_data.get('url', '').lower()
            page_type = page_data.get('type', 'other').lower()
            url_depth = url.count('/') - 2

            # Determine stage based on signals
            stage = self._determine_stage(url, page_type, url_depth)
            stage_mapping[page_id] = stage

        return stage_mapping

    def _determine_stage(self, url: str, page_type: str, url_depth: int) -> JourneyStage:
        """Determine journey stage for a page"""
        # ACTION stage - application/contact pages
        if any(kw in url for kw in ['apply', 'contact', 'register', 'enrol']):
            return JourneyStage.ACTION

        # DECISION stage - admissions, requirements, detailed programme info
        if page_type in ['admissions', 'application'] or 'admission' in url:
            return JourneyStage.DECISION

        # CONSIDERATION stage - programme pages, faculty, research
        if page_type in ['programme', 'faculty', 'research', 'course']:
            return JourneyStage.CONSIDERATION

        # RETENTION stage - student/alumni content
        if page_type in ['student_life', 'alumni'] or any(kw in url for kw in ['student', 'alumni']):
            return JourneyStage.RETENTION

        # AWARENESS stage - default for shallow pages
        if url_depth <= 2:
            return JourneyStage.AWARENESS

        # Default to CONSIDERATION for deeper pages
        return JourneyStage.CONSIDERATION

    def identify_typical_paths(
        self,
        persona_id: str,
        targeted_pages: List[str],
        stage_mapping: Dict[str, JourneyStage]
    ) -> List[JourneyPath]:
        """
        Identify typical journey paths

        Paths are identified by:
        1. Following LINKS_TO relationships
        2. Stage progression (awareness → consideration → decision → action)
        3. Frequency of transitions

        Args:
            persona_id: Persona identifier
            targeted_pages: List of page IDs
            stage_mapping: Mapping of pages to stages

        Returns:
            List of JourneyPath objects
        """
        paths = []

        # Get entry points as path starts
        entry_points = self.find_entry_points(persona_id, targeted_pages)

        # For each entry point, trace typical paths
        for idx, entry_point in enumerate(entry_points):
            path = self._trace_path_from_entry(
                entry_point.page_id,
                targeted_pages,
                stage_mapping,
                max_length=5
            )

            if path and len(path) >= 2:
                paths.append(JourneyPath(
                    path_id=f"path-{persona_id}-{idx+1}",
                    persona_id=persona_id,
                    page_sequence=path,
                    transition_probs=self._calculate_transition_probs(path),
                    stage_labels=[stage_mapping.get(p, JourneyStage.CONSIDERATION) for p in path],
                    frequency=3 - idx,  # Higher frequency for top entry points
                    completion_rate=0.6 - (idx * 0.1)  # Decreasing completion rate
                ))

        return paths[:5]  # Return top 5 paths

    def _trace_path_from_entry(
        self,
        start_page: str,
        targeted_pages: List[str],
        stage_mapping: Dict[str, JourneyStage],
        max_length: int = 5
    ) -> List[str]:
        """Trace a path from an entry point following links"""
        path = [start_page]
        current = start_page
        current_stage = stage_mapping.get(current, JourneyStage.AWARENESS)

        for _ in range(max_length - 1):
            # Get outgoing links
            next_pages = self._get_outgoing_links(current)

            # Filter to targeted pages
            next_pages = [p for p in next_pages if p in targeted_pages]

            if not next_pages:
                break

            # Prefer pages that progress the journey stage
            best_next = None
            for next_page in next_pages:
                next_stage = stage_mapping.get(next_page, JourneyStage.CONSIDERATION)
                if self._is_stage_progression(current_stage, next_stage):
                    best_next = next_page
                    current_stage = next_stage
                    break

            # If no progression found, take first available
            if not best_next:
                best_next = next_pages[0]

            path.append(best_next)
            current = best_next

        return path

    def _is_stage_progression(self, from_stage: JourneyStage, to_stage: JourneyStage) -> bool:
        """Check if transition represents stage progression"""
        stage_order = {
            JourneyStage.AWARENESS: 0,
            JourneyStage.CONSIDERATION: 1,
            JourneyStage.DECISION: 2,
            JourneyStage.ACTION: 3,
            JourneyStage.RETENTION: 4
        }
        return stage_order.get(to_stage, 0) > stage_order.get(from_stage, 0)

    def _calculate_transition_probs(self, path: List[str]) -> List[float]:
        """Calculate transition probabilities for a path"""
        # Simulate transition probabilities (would be from analytics in production)
        probs = []
        for i in range(len(path) - 1):
            # Higher probability early in path, decreasing as path progresses
            prob = 0.8 - (i * 0.1)
            probs.append(max(prob, 0.3))  # Minimum 30% transition probability
        return probs

    def _build_stage_info(self, stage_mapping: Dict[str, JourneyStage]) -> Dict[JourneyStage, JourneyStageInfo]:
        """Build stage info from stage mapping"""
        stages = {}

        # Group pages by stage
        stage_pages = defaultdict(set)
        for page_id, stage in stage_mapping.items():
            stage_pages[stage].add(page_id)

        # Create JourneyStageInfo for each stage
        for stage, page_ids in stage_pages.items():
            stages[stage] = JourneyStageInfo(
                stage=stage,
                page_ids=page_ids,
                typical_content_types=self._get_typical_content_types(page_ids)
            )

        return stages

    def _get_typical_content_types(self, page_ids: Set[str]) -> List[str]:
        """Get typical content types for a set of pages"""
        types = []
        for page_id in list(page_ids)[:5]:  # Sample first 5
            page_data = self._get_page_data(page_id)
            if page_data:
                types.append(page_data.get('type', 'other'))
        return list(set(types))

    def _get_page_data(self, page_id: str) -> Optional[Dict]:
        """Get page data from graph"""
        query = f"""
        MATCH (page:Page {{id: '{page_id}'}})
        RETURN page.id as id, page.url as url, page.title as title,
               page.type as type, page.importance as importance
        LIMIT 1
        """
        results = self.graph.execute_query(query)
        return results[0] if results else None

    def _count_incoming_links(self, page_id: str) -> int:
        """Count incoming links to a page"""
        query = f"""
        MATCH (p:Page)-[:LINKS_TO]->(target:Page {{id: '{page_id}'}})
        RETURN count(p) as count
        """
        results = self.graph.execute_query(query)
        return results[0]['count'] if results else 0

    def _get_outgoing_links(self, page_id: str) -> List[str]:
        """Get outgoing links from a page"""
        query = f"""
        MATCH (page:Page {{id: '{page_id}'}}) -[:LINKS_TO]-> (target:Page)
        RETURN target.id as page_id
        """
        results = self.graph.execute_query(query)
        return [r['page_id'] for r in results]

    def _estimate_traffic_sources(self, url: str) -> List[str]:
        """Estimate traffic sources based on URL"""
        sources = ['direct']

        if 'programmes' in url or 'mba' in url:
            sources.append('search')

        if 'news' in url or 'insights' in url:
            sources.extend(['search', 'social'])

        return sources

    def _identify_conversion_actions(self, url: str) -> List[str]:
        """Identify conversion actions from URL"""
        actions = []

        if 'apply' in url:
            actions.append('apply')
        if 'contact' in url:
            actions.append('contact')
        if 'register' in url:
            actions.append('register')

        return actions or ['enquire']

    def _create_empty_journey(self, persona_id: str) -> Journey:
        """Create empty journey when no data available"""
        return Journey(
            journey_id=f"journey-{persona_id}",
            persona_id=persona_id,
            persona_name=get_persona_name(persona_id)
        )
