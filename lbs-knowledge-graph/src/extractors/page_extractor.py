"""
PageExtractor - Extracts Page entities from parsed HTML data.

This extractor implements multi-signal classification for page type detection,
importance scoring, category assignment, and metadata extraction.

Key Features:
- URL pattern-based page type detection
- Multi-signal classification (URL + content + metadata)
- Importance scoring based on URL depth and centrality
- Category assignment using site taxonomy
- Breadcrumb and metadata extraction
"""

import hashlib
import logging
import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from ..models.entities import Page
from ..models.enums import PageType


logger = logging.getLogger(__name__)


class PageExtractor:
    """
    Extracts Page entities from parsed JSON data.

    Uses multi-signal classification to determine page type, category,
    and importance based on URL patterns, content analysis, and metadata.
    """

    # URL namespace for UUID generation (standard URL namespace)
    URL_NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')

    # URL pattern mapping for page type detection
    URL_PATTERNS = {
        PageType.HOMEPAGE: [
            (r'^https?://[^/]+/?$', 1.0),  # Root domain only
        ],
        PageType.PROGRAM: [
            (r'/programmes?/', 0.9),
            (r'/programs?/', 0.9),
            (r'/mba/', 0.95),
            (r'/masters?/', 0.9),
            (r'/phd/', 0.95),
            (r'/executive-education/', 0.85),
        ],
        PageType.FACULTY: [
            (r'/faculty-and-research/faculty/', 0.95),
            (r'/faculty/', 0.9),
            (r'/people/faculty/', 0.9),
        ],
        PageType.RESEARCH: [
            (r'/research/', 0.85),
            (r'/faculty-and-research/research', 0.9),
            (r'/publications/', 0.8),
            (r'/working-papers/', 0.8),
        ],
        PageType.NEWS: [
            (r'/news/', 0.95),
            (r'/insights/', 0.85),
            (r'/articles/', 0.8),
        ],
        PageType.EVENT: [
            (r'/events/', 0.95),
            (r'/webinars/', 0.9),
        ],
        PageType.ADMISSIONS: [
            (r'/admissions/', 0.95),
            (r'/apply/', 0.9),
            (r'/how-to-apply/', 0.9),
        ],
        PageType.STUDENT_LIFE: [
            (r'/student-life/', 0.95),
            (r'/campus/', 0.85),
            (r'/careers/', 0.8),
        ],
        PageType.ALUMNI: [
            (r'/alumni/', 0.95),
            (r'/giving/', 0.85),
        ],
        PageType.ABOUT: [
            (r'/about/', 0.95),
            (r'/mission/', 0.9),
            (r'/history/', 0.9),
        ],
        PageType.CONTACT: [
            (r'/contact', 0.95),
            (r'/locations/', 0.85),
        ],
    }

    # Category extraction rules (from SITE_TAXONOMY.md)
    CATEGORY_PATTERNS = {
        r'/programmes?/': 'Programmes & Education',
        r'/programs?/': 'Programmes & Education',
        r'/executive-education/': 'Programmes & Education',
        r'/courses?/': 'Programmes & Education',
        r'/faculty-and-research/': 'Faculty & Research',
        r'/research/': 'Faculty & Research',
        r'/departments?/': 'Faculty & Research',
        r'/admissions?/': 'Admissions & Recruitment',
        r'/apply/': 'Admissions & Recruitment',
        r'/scholarships?/': 'Admissions & Recruitment',
        r'/student-life/': 'Student Experience',
        r'/careers?/': 'Student Experience',
        r'/campus/': 'Student Experience',
        r'/alumni/': 'Alumni & Community',
        r'/giving/': 'Alumni & Community',
        r'/about/': 'About & Governance',
        r'/contact': 'About & Governance',
        r'/governance/': 'About & Governance',
        r'/news/': 'News & Events',
        r'/events?/': 'News & Events',
        r'/insights/': 'News & Events',
    }

    def extract_page_entity(self, parsed_data: Dict[str, Any]) -> Page:
        """
        Extract Page entity from parsed data.

        Args:
            parsed_data: Output from HTMLParser.parse_html() containing:
                - url: str
                - metadata: Dict
                - dom: Dict
                - links: List[Dict]
                - text_hashes: Dict[str, str]
                - nextjs_data: Optional[Dict]

        Returns:
            Page entity with all fields populated

        Raises:
            ValueError: If required fields are missing
            KeyError: If parsed_data structure is invalid
        """
        try:
            url = parsed_data['url']
            metadata = parsed_data.get('metadata', {})
            dom = parsed_data.get('dom', {})
            links = parsed_data.get('links', [])
            text_hashes = parsed_data.get('text_hashes', {})

            # Generate stable UUID from URL
            page_id = self._generate_uuid_from_url(url)

            # Calculate content hashes
            html_hash = self._calculate_html_hash(dom)
            content_hash = self._calculate_content_hash(text_hashes)

            # Extract page type
            page_type = self.extract_page_type(url, metadata, parsed_data)

            # Extract category
            category = self.extract_categories(url, metadata)

            # Extract metadata
            title = self._extract_title(metadata, dom)
            description = metadata.get('description')
            keywords = self._extract_keywords(metadata)

            # Calculate analytics
            depth = self._calculate_depth(url)
            outbound_links = len([link for link in links if link.get('type') == 'internal'])
            importance = self.calculate_importance(url, 0, depth)  # inbound_links populated later

            # Extract temporal data
            published_at = self._extract_publish_date(metadata, parsed_data)

            # Create Page entity
            page = Page(
                id=page_id,
                url=self._normalize_url(url),
                title=title,
                description=description,
                type=page_type,
                category=category,
                language=metadata.get('language', 'en'),
                hash=html_hash,
                content_hash=content_hash,
                version=1,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                fetched_at=datetime.now(),
                published_at=published_at,
                keywords=keywords,
                og_image=metadata.get('og_image'),
                og_description=metadata.get('og_description'),
                importance=importance,
                depth=depth,
                inbound_links=0,
                outbound_links=outbound_links,
                metadata=self._extract_custom_metadata(parsed_data)
            )

            logger.info(f"Extracted Page entity: {page.url} (type={page.type.value}, category={page.category})")
            return page

        except KeyError as e:
            logger.error(f"Missing required field in parsed_data: {e}")
            raise ValueError(f"Invalid parsed_data structure: missing {e}")
        except Exception as e:
            logger.error(f"Error extracting Page entity: {e}")
            raise

    def extract_page_type(self, url: str, metadata: Dict[str, Any], parsed_data: Dict[str, Any]) -> PageType:
        """
        Multi-signal page type classification.

        Priority:
        1. URL pattern matching (highest confidence)
        2. Schema.org markup in metadata
        3. Breadcrumb analysis
        4. Content analysis (title, headings)

        Args:
            url: Page URL
            metadata: Page metadata
            parsed_data: Full parsed data including DOM

        Returns:
            PageType classification
        """
        # 1. URL pattern matching
        best_match = None
        best_confidence = 0.0

        for page_type, patterns in self.URL_PATTERNS.items():
            for pattern, confidence in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    if confidence > best_confidence:
                        best_match = page_type
                        best_confidence = confidence

        if best_match and best_confidence >= 0.85:
            logger.debug(f"Page type detected via URL pattern: {best_match.value} (confidence={best_confidence})")
            return best_match

        # 2. Schema.org analysis
        schema_type = self._extract_schema_type(metadata)
        if schema_type:
            if schema_type in ['Course', 'EducationalOrganization']:
                return PageType.PROGRAM
            if schema_type == 'Person':
                return PageType.FACULTY
            if schema_type == 'NewsArticle':
                return PageType.NEWS
            if schema_type == 'Event':
                return PageType.EVENT

        # 3. Content-based classification
        title = metadata.get('title', '').lower()
        if any(kw in title for kw in ['mba', 'masters', 'phd', 'programme', 'program']):
            return PageType.PROGRAM
        if any(kw in title for kw in ['professor', 'dr.', 'faculty']):
            return PageType.FACULTY
        if any(kw in title for kw in ['news', 'article', 'insight']):
            return PageType.NEWS

        # Default to OTHER if no strong signals
        logger.debug(f"Page type defaulted to OTHER for URL: {url}")
        return PageType.OTHER

    def calculate_importance(self, url: str, backlinks: int = 0, depth: Optional[int] = None) -> float:
        """
        Calculate page importance score (0-1) based on centrality and backlinks.

        Factors:
        - URL depth (closer to homepage = higher importance)
        - Number of backlinks
        - URL authority signals (homepage, main sections)

        Args:
            url: Page URL
            backlinks: Number of inbound links
            depth: URL depth (calculated if not provided)

        Returns:
            Importance score between 0.0 and 1.0
        """
        if depth is None:
            depth = self._calculate_depth(url)

        # Base score from depth (inverse relationship)
        # Homepage (depth=0) = 1.0, depth=5 = 0.5, depth=10+ = 0.0
        depth_score = max(0.0, 1.0 - (depth * 0.1))

        # Backlink score (logarithmic scaling)
        backlink_score = min(1.0, (backlinks / 10.0) if backlinks > 0 else 0.0)

        # Authority signals
        authority_score = 0.0
        if re.search(r'^https?://[^/]+/?$', url):
            authority_score = 1.0  # Homepage
        elif any(pattern in url for pattern in ['/programmes/', '/faculty/', '/admissions/']):
            authority_score = 0.8  # Main sections

        # Weighted average
        importance = (
            depth_score * 0.4 +
            backlink_score * 0.4 +
            authority_score * 0.2
        )

        return round(importance, 3)

    def extract_categories(self, url: str, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Extract primary category from URL structure and metadata.

        Uses pattern matching against SITE_TAXONOMY category rules.

        Args:
            url: Page URL
            metadata: Page metadata (may contain breadcrumbs)

        Returns:
            Primary category name or None
        """
        # Check URL patterns
        for pattern, category in self.CATEGORY_PATTERNS.items():
            if re.search(pattern, url, re.IGNORECASE):
                return category

        # Fallback: extract from URL path
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) >= 1:
            return path_parts[0].replace('-', ' ').title()

        return None

    def _generate_uuid_from_url(self, url: str) -> str:
        """Generate deterministic UUID v5 from URL."""
        return str(uuid.uuid5(self.URL_NAMESPACE, url))

    def _normalize_url(self, url: str) -> str:
        """Normalize URL (remove trailing slashes, fragments, etc.)."""
        url = url.rstrip('/')
        url = url.split('#')[0]  # Remove fragments
        return url

    def _calculate_depth(self, url: str) -> int:
        """Calculate URL depth (distance from homepage)."""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        return len(path_parts)

    def _calculate_html_hash(self, dom: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of DOM structure."""
        dom_str = str(dom).encode('utf-8')
        return hashlib.sha256(dom_str).hexdigest()

    def _calculate_content_hash(self, text_hashes: Dict[str, str]) -> str:
        """Calculate SHA-256 hash of all text content."""
        # Concatenate all text values in sorted order for consistency
        sorted_texts = sorted(text_hashes.values())
        content_str = ''.join(sorted_texts).encode('utf-8')
        return hashlib.sha256(content_str).hexdigest()

    def _extract_title(self, metadata: Dict[str, Any], dom: Dict[str, Any]) -> str:
        """Extract page title from metadata or DOM."""
        title = metadata.get('title')
        if title:
            return title

        # Fallback: search for h1 in DOM
        # This is a simplified implementation - actual implementation would traverse DOM
        return "Untitled Page"

    def _extract_keywords(self, metadata: Dict[str, Any]) -> List[str]:
        """Extract keywords from metadata."""
        keywords = metadata.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [kw.strip() for kw in keywords.split(',')]
        return keywords

    def _extract_schema_type(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract Schema.org type from metadata."""
        schema = metadata.get('schema', {})
        if isinstance(schema, dict):
            return schema.get('@type')
        return None

    def _extract_publish_date(self, metadata: Dict[str, Any], parsed_data: Dict[str, Any]) -> Optional[datetime]:
        """Extract publication date from metadata."""
        # Check common metadata fields
        date_str = metadata.get('published_time') or metadata.get('article:published_time')
        if date_str:
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        return None

    def _extract_custom_metadata(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract custom metadata for storage."""
        metadata = {}

        # Store NextJS data if available
        if 'nextjs_data' in parsed_data and parsed_data['nextjs_data']:
            metadata['nextjs_data'] = parsed_data['nextjs_data']

        # Store breadcrumbs if available
        if 'breadcrumbs' in parsed_data.get('metadata', {}):
            metadata['breadcrumbs'] = parsed_data['metadata']['breadcrumbs']

        return metadata
