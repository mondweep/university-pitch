#!/usr/bin/env python3
"""
LBS Knowledge Graph - HTML Parser
Converts raw HTML to structured JSON with content hashing
"""

import json
import hashlib
import re
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import logging

from bs4 import BeautifulSoup, Tag, NavigableString
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


class HTMLParser:
    """Parse HTML into structured JSON with content hashing"""

    def __init__(self):
        """Initialize parser"""
        self.text_hashes: Dict[str, str] = {}  # hash -> text mapping
        self.hash_usage: Dict[str, int] = {}    # hash -> usage count

    def generate_hash(self, text: str) -> str:
        """
        Generate SHA-256 hash for text content

        Args:
            text: Text to hash

        Returns:
            Hash string
        """
        # Normalize whitespace
        normalized = ' '.join(text.split())

        # Generate hash
        hash_obj = hashlib.sha256(normalized.encode('utf-8'))
        return hash_obj.hexdigest()

    def extract_text_content(self, element: Tag) -> Optional[str]:
        """
        Extract and clean text from element

        Args:
            element: BeautifulSoup Tag

        Returns:
            Cleaned text or None
        """
        if isinstance(element, NavigableString):
            text = str(element).strip()
            return text if text else None

        # Get direct text (not from children)
        texts = []
        for child in element.children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    texts.append(text)

        combined = ' '.join(texts)
        return combined if combined else None

    def parse_element(self, element: Tag, depth: int = 0) -> Dict[str, Any]:
        """
        Recursively parse HTML element into JSON structure

        Args:
            element: BeautifulSoup Tag
            depth: Current depth in DOM tree

        Returns:
            Dict representing element structure
        """
        result = {
            'tag': element.name,
            'depth': depth
        }

        # Extract attributes (exclude noisy ones)
        attrs = {}
        excluded_attrs = {'data-reactid', 'data-react-checksum'}

        for key, value in element.attrs.items():
            if key not in excluded_attrs:
                # Handle list values (like class)
                if isinstance(value, list):
                    attrs[key] = ' '.join(value)
                else:
                    attrs[key] = value

        if attrs:
            result['attributes'] = attrs

        # Extract direct text content
        text = self.extract_text_content(element)

        if text:
            # Generate hash for text
            text_hash = self.generate_hash(text)

            # Store text (if not already stored)
            if text_hash not in self.text_hashes:
                self.text_hashes[text_hash] = text
                self.hash_usage[text_hash] = 0

            self.hash_usage[text_hash] += 1

            result['text_hash'] = text_hash

        # Parse children
        children = []
        for child in element.children:
            if isinstance(child, Tag):
                child_data = self.parse_element(child, depth + 1)
                children.append(child_data)

        if children:
            result['children'] = children

        return result

    def extract_nextjs_data(self, soup: BeautifulSoup) -> Optional[Dict]:
        """
        Extract Next.js __NEXT_DATA__ JSON if present

        Args:
            soup: BeautifulSoup object

        Returns:
            Parsed JSON data or None
        """
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})

        if script_tag and script_tag.string:
            try:
                data = json.loads(script_tag.string)
                logger.info("Found __NEXT_DATA__ content")
                return data
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse __NEXT_DATA__: {e}")

        return None

    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract page metadata (title, description, etc.)

        Args:
            soup: BeautifulSoup object

        Returns:
            Metadata dict
        """
        metadata = {}

        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()

        # Meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name') or tag.get('property')
            content = tag.get('content')

            if name and content:
                # Normalize meta tag names
                if name.startswith('og:'):
                    key = f"og_{name[3:]}"
                elif name.startswith('twitter:'):
                    key = f"twitter_{name[8:]}"
                else:
                    key = name

                metadata[key] = content

        # Canonical URL
        canonical = soup.find('link', {'rel': 'canonical'})
        if canonical and canonical.get('href'):
            metadata['canonical_url'] = canonical['href']

        # Language
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            metadata['language'] = html_tag['lang']

        return metadata

    def extract_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract all links from page

        Args:
            soup: BeautifulSoup object

        Returns:
            List of link dicts
        """
        links = []

        for a_tag in soup.find_all('a', href=True):
            link = {
                'href': a_tag['href'],
                'text': a_tag.get_text().strip()
            }

            # Link type
            if a_tag.get('href', '').startswith('http'):
                link['type'] = 'external'
            elif a_tag.get('href', '').startswith('/'):
                link['type'] = 'internal'
            elif a_tag.get('href', '').startswith('#'):
                link['type'] = 'anchor'
            else:
                link['type'] = 'relative'

            if link['text']:  # Only include links with text
                links.append(link)

        logger.info(f"Extracted {len(links)} links")
        return links

    def parse_html(self, html: str, url: str) -> Dict[str, Any]:
        """
        Parse HTML into complete structured representation

        Args:
            html: Raw HTML string
            url: Page URL

        Returns:
            Complete parsed structure
        """
        # Reset for new page
        self.text_hashes = {}
        self.hash_usage = {}

        logger.info(f"Parsing HTML for {url}")

        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style tags (keep only content)
        for script in soup(['script', 'style']):
            script.decompose()

        # Extract components
        dom_structure = self.parse_element(soup.find('body') or soup.html)
        metadata = self.extract_metadata(soup)
        nextjs_data = self.extract_nextjs_data(soup)
        links = self.extract_links(soup)

        # Build result
        result = {
            'url': url,
            'metadata': metadata,
            'dom': dom_structure,
            'links': links,
            'text_hashes': self.text_hashes,
            'hash_usage': self.hash_usage,
            'nextjs_data': nextjs_data,
            'stats': {
                'unique_text_items': len(self.text_hashes),
                'total_links': len(links),
                'has_nextjs_data': nextjs_data is not None
            }
        }

        logger.info(f"Parsed {len(self.text_hashes)} unique text items")

        return result

    def parse_file(self, html_file: Path, output_dir: Path) -> Dict[str, Path]:
        """
        Parse HTML file and save structured output

        Args:
            html_file: Path to HTML file
            output_dir: Directory for output

        Returns:
            Dict mapping output type to file path
        """
        logger.info(f"Processing {html_file.name}")

        # Read HTML
        with open(html_file, 'r', encoding='utf-8') as f:
            html = f.read()

        # Load metadata if exists
        meta_file = html_file.parent / f"{html_file.name}.meta.json"
        url = "unknown"

        if meta_file.exists():
            with open(meta_file, 'r') as f:
                meta = json.load(f)
                url = meta.get('url', 'unknown')

        # Parse
        parsed = self.parse_html(html, url)

        # Create output directory for this page
        page_dir = output_dir / html_file.stem
        page_dir.mkdir(parents=True, exist_ok=True)

        # Save DOM structure
        dom_file = page_dir / 'dom.json'
        with open(dom_file, 'w', encoding='utf-8') as f:
            json.dump(parsed['dom'], f, indent=2)

        # Save text hashes
        text_file = page_dir / 'text.json'
        with open(text_file, 'w', encoding='utf-8') as f:
            json.dump(parsed['text_hashes'], f, indent=2, ensure_ascii=False)

        # Save metadata
        metadata_file = page_dir / 'metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(parsed['metadata'], f, indent=2)

        # Save links
        links_file = page_dir / 'links.json'
        with open(links_file, 'w', encoding='utf-8') as f:
            json.dump(parsed['links'], f, indent=2)

        # Save Next.js data if present
        if parsed['nextjs_data']:
            nextjs_file = page_dir / 'nextjs-data.json'
            with open(nextjs_file, 'w', encoding='utf-8') as f:
                json.dump(parsed['nextjs_data'], f, indent=2)

        logger.info(f"✓ Saved parsed data to {page_dir}")

        return {
            'dom': dom_file,
            'text': text_file,
            'metadata': metadata_file,
            'links': links_file
        }


def main():
    """Main entry point"""
    import sys
    from dotenv import load_dotenv
    import os

    load_dotenv()

    # Directories
    input_dir = Path(os.getenv('RAW_HTML_DIR', './content-repo/raw'))
    output_dir = Path(os.getenv('PARSED_JSON_DIR', './content-repo/parsed'))

    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse all HTML files
    parser = HTMLParser()
    html_files = list(input_dir.glob('*.html'))

    logger.info(f"Found {len(html_files)} HTML files to parse")

    for html_file in html_files:
        try:
            parser.parse_file(html_file, output_dir)
        except Exception as e:
            logger.error(f"Failed to parse {html_file}: {e}")

    logger.info(f"Parsing complete. Output saved to {output_dir}")


if __name__ == '__main__':
    main()
