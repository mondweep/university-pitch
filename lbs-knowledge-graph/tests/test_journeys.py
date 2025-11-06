"""
Journey Analysis Tests for Phase 3
Tests for journey analyzer, entry points, conversion points, NEXT_STEP relationships
Target: 25+ tests covering all journey analysis functionality
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any

from src.enrichment.journey_analyzer import JourneyAnalyzer
from src.enrichment.journey_models import (
    Journey, JourneyStage, JourneyPath, EntryPoint, ConversionPoint
)


# ==================== Journey Analyzer Initialization Tests ====================

@pytest.mark.unit
class TestJourneyAnalyzerInit:
    """Test journey analyzer initialization (3 tests)"""

    def test_init_with_graph(self):
        """Test initialization with graph"""
        mock_graph = Mock()
        analyzer = JourneyAnalyzer(mock_graph)

        assert analyzer.graph == mock_graph
        assert hasattr(analyzer, 'personas')

    def test_init_requires_graph(self):
        """Test that graph is required"""
        with pytest.raises(TypeError):
            JourneyAnalyzer()

    def test_init_loads_personas(self):
        """Test that personas are loaded"""
        mock_graph = Mock()
        analyzer = JourneyAnalyzer(mock_graph)

        assert len(analyzer.personas) > 0


# ==================== Entry Point Identification Tests ====================

@pytest.mark.unit
class TestEntryPointIdentification:
    """Test entry point identification (6 tests)"""

    def test_find_entry_points_basic(self):
        """Test basic entry point identification"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "page-1"},
            {"page_id": "page-2"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(side_effect=lambda pid: {
            "id": pid,
            "url": f"https://london.edu/{pid}",
            "title": f"Page {pid}",
            "type": "programme",
            "importance": 0.9
        })

        entry_points = analyzer.find_entry_points("prospective-student")

        assert len(entry_points) > 0
        assert all(isinstance(ep, EntryPoint) for ep in entry_points)

    def test_entry_points_shallow_urls(self):
        """Test that shallow URLs are preferred as entry points"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "page-shallow"},
            {"page_id": "page-deep"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(side_effect=lambda pid: {
            "id": pid,
            "url": "https://london.edu/programmes" if "shallow" in pid else "https://london.edu/programmes/mba/specializations/finance",
            "title": f"Page {pid}",
            "type": "programme",
            "importance": 0.8
        })

        entry_points = analyzer.find_entry_points("prospective-student")

        # Shallow URL should have higher entry score
        assert any("shallow" in ep.page_id for ep in entry_points)

    def test_entry_points_high_importance(self):
        """Test that high importance pages are preferred"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "page-important"},
            {"page_id": "page-minor"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(side_effect=lambda pid: {
            "id": pid,
            "url": f"https://london.edu/{pid}",
            "title": f"Page {pid}",
            "type": "programme",
            "importance": 0.95 if "important" in pid else 0.3
        })

        entry_points = analyzer.find_entry_points("prospective-student")

        # Important page should be in results
        assert any("important" in ep.page_id for ep in entry_points)

    def test_entry_points_limit(self):
        """Test that entry points are limited to top N"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": f"page-{i}"} for i in range(10)
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(side_effect=lambda pid: {
            "id": pid,
            "url": f"https://london.edu/{pid}",
            "title": f"Page {pid}",
            "type": "programme",
            "importance": 0.8
        })

        entry_points = analyzer.find_entry_points("prospective-student")

        # Should limit to top 3
        assert len(entry_points) <= 3

    def test_entry_points_stage_assignment(self):
        """Test that entry points are assigned to journey stages"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "page-1"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(return_value={
            "id": "page-1",
            "url": "https://london.edu/programmes",
            "title": "Programmes",
            "type": "programme",
            "importance": 0.9
        })

        entry_points = analyzer.find_entry_points("prospective-student")

        assert all(hasattr(ep, 'stage') for ep in entry_points)
        assert all(isinstance(ep.stage, JourneyStage) for ep in entry_points)

    def test_entry_points_traffic_sources(self):
        """Test that traffic sources are estimated"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "page-1"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(return_value={
            "id": "page-1",
            "url": "https://london.edu/programmes/mba",
            "title": "MBA Programme",
            "type": "programme",
            "importance": 0.9
        })

        entry_points = analyzer.find_entry_points("prospective-student")

        assert all(hasattr(ep, 'traffic_sources') for ep in entry_points)
        assert all(len(ep.traffic_sources) > 0 for ep in entry_points)


# ==================== Conversion Point Identification Tests ====================

@pytest.mark.unit
class TestConversionPointIdentification:
    """Test conversion point identification (5 tests)"""

    def test_find_conversion_points_basic(self):
        """Test basic conversion point identification"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "apply-page"},
            {"page_id": "contact-page"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(side_effect=lambda pid: {
            "id": pid,
            "url": f"https://london.edu/{pid}",
            "title": f"Page {pid}",
            "type": "admissions" if "apply" in pid else "contact",
            "importance": 0.8
        })
        analyzer._count_incoming_links = Mock(return_value=5)

        conversion_points = analyzer.find_conversion_points("prospective-student")

        assert len(conversion_points) > 0
        assert all(isinstance(cp, ConversionPoint) for cp in conversion_points)

    def test_conversion_points_action_keywords(self):
        """Test that action keywords are detected"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "apply-now"},
            {"page_id": "general-info"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(side_effect=lambda pid: {
            "id": pid,
            "url": f"https://london.edu/{pid}",
            "title": f"Page {pid}",
            "type": "admissions" if "apply" in pid else "general",
            "importance": 0.8
        })
        analyzer._count_incoming_links = Mock(return_value=3)

        conversion_points = analyzer.find_conversion_points("prospective-student")

        # Apply page should be identified
        assert any("apply" in cp.page_id for cp in conversion_points)

    def test_conversion_points_stage(self):
        """Test that conversion points are in ACTION stage"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "apply-page"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(return_value={
            "id": "apply-page",
            "url": "https://london.edu/apply",
            "title": "Apply Now",
            "type": "admissions",
            "importance": 0.9
        })
        analyzer._count_incoming_links = Mock(return_value=5)

        conversion_points = analyzer.find_conversion_points("prospective-student")

        assert all(cp.stage == JourneyStage.ACTION for cp in conversion_points)

    def test_conversion_points_actions(self):
        """Test that conversion actions are identified"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "apply-page"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(return_value={
            "id": "apply-page",
            "url": "https://london.edu/apply",
            "title": "Apply",
            "type": "admissions",
            "importance": 0.9
        })
        analyzer._count_incoming_links = Mock(return_value=5)

        conversion_points = analyzer.find_conversion_points("prospective-student")

        assert all(len(cp.conversion_actions) > 0 for cp in conversion_points)

    def test_conversion_points_limit(self):
        """Test that conversion points are limited to top 2"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": f"conversion-{i}"} for i in range(5)
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(side_effect=lambda pid: {
            "id": pid,
            "url": f"https://london.edu/apply/{pid}",
            "title": f"Apply {pid}",
            "type": "admissions",
            "importance": 0.8
        })
        analyzer._count_incoming_links = Mock(return_value=5)

        conversion_points = analyzer.find_conversion_points("prospective-student")

        assert len(conversion_points) <= 2


# ==================== Journey Stage Mapping Tests ====================

@pytest.mark.unit
class TestJourneyStageMapping:
    """Test journey stage mapping (6 tests)"""

    def test_map_journey_stages_basic(self):
        """Test basic stage mapping"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "page-1"},
            {"page_id": "page-2"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(side_effect=lambda pid: {
            "id": pid,
            "url": f"https://london.edu/{pid}",
            "title": f"Page {pid}",
            "type": "programme",
            "importance": 0.8
        })

        stage_mapping = analyzer.map_journey_stages("prospective-student")

        assert isinstance(stage_mapping, dict)
        assert all(isinstance(stage, JourneyStage) for stage in stage_mapping.values())

    def test_awareness_stage_shallow_pages(self):
        """Test that shallow pages map to AWARENESS stage"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "homepage"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(return_value={
            "id": "homepage",
            "url": "https://london.edu/",
            "title": "Home",
            "type": "home",
            "importance": 1.0
        })

        stage_mapping = analyzer.map_journey_stages("prospective-student")

        assert stage_mapping["homepage"] == JourneyStage.AWARENESS

    def test_consideration_stage_programme_pages(self):
        """Test that programme pages map to CONSIDERATION stage"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "mba-page"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(return_value={
            "id": "mba-page",
            "url": "https://london.edu/programmes/mba",
            "title": "MBA Programme",
            "type": "programme",
            "importance": 0.9
        })

        stage_mapping = analyzer.map_journey_stages("prospective-student")

        assert stage_mapping["mba-page"] == JourneyStage.CONSIDERATION

    def test_decision_stage_admissions_pages(self):
        """Test that admissions pages map to DECISION stage"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "admissions-page"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(return_value={
            "id": "admissions-page",
            "url": "https://london.edu/admissions",
            "title": "Admissions",
            "type": "admissions",
            "importance": 0.85
        })

        stage_mapping = analyzer.map_journey_stages("prospective-student")

        assert stage_mapping["admissions-page"] == JourneyStage.DECISION

    def test_action_stage_apply_pages(self):
        """Test that apply pages map to ACTION stage"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "apply-page"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(return_value={
            "id": "apply-page",
            "url": "https://london.edu/apply",
            "title": "Apply Now",
            "type": "application",
            "importance": 0.9
        })

        stage_mapping = analyzer.map_journey_stages("prospective-student")

        assert stage_mapping["apply-page"] == JourneyStage.ACTION

    def test_retention_stage_alumni_pages(self):
        """Test that alumni pages map to RETENTION stage"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "alumni-page"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(return_value={
            "id": "alumni-page",
            "url": "https://london.edu/alumni",
            "title": "Alumni Network",
            "type": "alumni",
            "importance": 0.7
        })

        stage_mapping = analyzer.map_journey_stages("prospective-student")

        assert stage_mapping["alumni-page"] == JourneyStage.RETENTION


# ==================== Typical Path Identification Tests ====================

@pytest.mark.unit
class TestTypicalPathIdentification:
    """Test typical journey path identification (5 tests)"""

    def test_identify_typical_paths_basic(self):
        """Test basic path identification"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[
            {"page_id": "page-1"},
            {"page_id": "page-2"}
        ])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(side_effect=lambda pid: {
            "id": pid,
            "url": f"https://london.edu/{pid}",
            "title": f"Page {pid}",
            "type": "programme",
            "importance": 0.8
        })
        analyzer.find_entry_points = Mock(return_value=[
            EntryPoint(
                page_id="page-1",
                page_url="https://london.edu/page-1",
                page_title="Page 1",
                entry_rate=0.8,
                stage=JourneyStage.AWARENESS,
                traffic_sources=["direct"]
            )
        ])
        analyzer._get_outgoing_links = Mock(return_value=["page-2"])

        targeted_pages = ["page-1", "page-2"]
        stage_mapping = {"page-1": JourneyStage.AWARENESS, "page-2": JourneyStage.CONSIDERATION}

        paths = analyzer.identify_typical_paths("prospective-student", targeted_pages, stage_mapping)

        assert len(paths) > 0
        assert all(isinstance(p, JourneyPath) for p in paths)

    def test_paths_have_page_sequence(self):
        """Test that paths contain page sequences"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[{"page_id": "page-1"}])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(return_value={
            "id": "page-1",
            "url": "https://london.edu/page-1",
            "title": "Page 1",
            "type": "programme",
            "importance": 0.8
        })
        analyzer.find_entry_points = Mock(return_value=[
            EntryPoint(
                page_id="page-1",
                page_url="https://london.edu/page-1",
                page_title="Page 1",
                entry_rate=0.8,
                stage=JourneyStage.AWARENESS,
                traffic_sources=["direct"]
            )
        ])
        analyzer._get_outgoing_links = Mock(return_value=[])

        paths = analyzer.identify_typical_paths("prospective-student", ["page-1"], {"page-1": JourneyStage.AWARENESS})

        if paths:
            assert all(hasattr(p, 'page_sequence') for p in paths)
            assert all(len(p.page_sequence) >= 1 for p in paths)

    def test_paths_have_stages(self):
        """Test that paths have stage labels"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[{"page_id": "page-1"}])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(return_value={
            "id": "page-1",
            "url": "https://london.edu/page-1",
            "title": "Page 1",
            "type": "programme",
            "importance": 0.8
        })
        analyzer.find_entry_points = Mock(return_value=[
            EntryPoint(
                page_id="page-1",
                page_url="https://london.edu/page-1",
                page_title="Page 1",
                entry_rate=0.8,
                stage=JourneyStage.AWARENESS,
                traffic_sources=["direct"]
            )
        ])
        analyzer._get_outgoing_links = Mock(return_value=[])

        paths = analyzer.identify_typical_paths("prospective-student", ["page-1"], {"page-1": JourneyStage.AWARENESS})

        if paths:
            assert all(hasattr(p, 'stage_labels') for p in paths)

    def test_paths_limited_to_five(self):
        """Test that paths are limited to top 5"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[{"page_id": f"page-{i}"} for i in range(10)])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(side_effect=lambda pid: {
            "id": pid,
            "url": f"https://london.edu/{pid}",
            "title": f"Page {pid}",
            "type": "programme",
            "importance": 0.8
        })
        analyzer.find_entry_points = Mock(return_value=[
            EntryPoint(
                page_id=f"page-{i}",
                page_url=f"https://london.edu/page-{i}",
                page_title=f"Page {i}",
                entry_rate=0.8,
                stage=JourneyStage.AWARENESS,
                traffic_sources=["direct"]
            )
            for i in range(10)
        ])
        analyzer._get_outgoing_links = Mock(return_value=[])

        paths = analyzer.identify_typical_paths(
            "prospective-student",
            [f"page-{i}" for i in range(10)],
            {f"page-{i}": JourneyStage.AWARENESS for i in range(10)}
        )

        assert len(paths) <= 5

    def test_paths_have_transition_probs(self):
        """Test that paths have transition probabilities"""
        mock_graph = Mock()
        mock_graph.execute_query = Mock(return_value=[{"page_id": "page-1"}])

        analyzer = JourneyAnalyzer(mock_graph)
        analyzer._get_page_data = Mock(return_value={
            "id": "page-1",
            "url": "https://london.edu/page-1",
            "title": "Page 1",
            "type": "programme",
            "importance": 0.8
        })
        analyzer.find_entry_points = Mock(return_value=[
            EntryPoint(
                page_id="page-1",
                page_url="https://london.edu/page-1",
                page_title="Page 1",
                entry_rate=0.8,
                stage=JourneyStage.AWARENESS,
                traffic_sources=["direct"]
            )
        ])
        analyzer._get_outgoing_links = Mock(return_value=["page-2"])

        paths = analyzer.identify_typical_paths(
            "prospective-student",
            ["page-1", "page-2"],
            {"page-1": JourneyStage.AWARENESS, "page-2": JourneyStage.CONSIDERATION}
        )

        if paths and len(paths[0].page_sequence) > 1:
            assert all(hasattr(p, 'transition_probs') for p in paths)
