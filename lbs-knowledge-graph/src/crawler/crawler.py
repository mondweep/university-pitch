#!/usr/bin/env python3
"""
LBS Knowledge Graph - Web Crawler
Crawls london.edu and saves HTML to content repository
"""

import os
import time
import hashlib
import json
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
from pathlib import Path
import logging

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LBSCrawler:
    """Web crawler for London Business School website"""

    def __init__(
        self,
        base_url: str = "https://london.edu",
        output_dir: str = "./content-repo/raw",
        max_pages: int = 10,
        crawl_delay_ms: int = 2000,
        respect_robots: bool = True
    ):
        """
        Initialize crawler

        Args:
            base_url: Base URL to crawl
            output_dir: Directory to save raw HTML
            max_pages: Maximum number of pages to crawl
            crawl_delay_ms: Delay between requests in milliseconds
            respect_robots: Whether to respect robots.txt
        """
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.max_pages = max_pages
        self.crawl_delay_ms = crawl_delay_ms
        self.respect_robots = respect_robots

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': os.getenv(
                'USER_AGENT',
                'LBS-KnowledgeGraph-Bot/1.0 (+https://london.edu/bot)'
            )
        })

        # Tracking
        self.visited_urls: Set[str] = set()
        self.queued_urls: List[str] = []
        self.failed_urls: List[Dict] = []

        logger.info(f"Crawler initialized for {base_url}")

    def normalize_url(self, url: str) -> str:
        """Normalize URL for consistent comparison"""
        parsed = urlparse(url)
        # Remove fragment, keep path and query
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized.rstrip('/')

    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled"""
        parsed = urlparse(url)

        # Must be same domain
        if parsed.netloc and parsed.netloc not in self.base_url:
            return False

        # Exclude certain paths
        excluded_paths = ['/api/', '/admin/', '/login', '/logout', '/search']
        if any(path in parsed.path for path in excluded_paths):
            return False

        # Exclude file downloads
        excluded_extensions = ['.pdf', '.jpg', '.png', '.zip', '.doc', '.xls']
        if any(parsed.path.lower().endswith(ext) for ext in excluded_extensions):
            return False

        return True

    def generate_filename(self, url: str) -> str:
        """Generate filename for saved HTML"""
        # Use URL hash for filename
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]

        # Extract meaningful part of path
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]

        if path_parts:
            # Use last part of path
            filename = f"{path_parts[-1]}_{url_hash}.html"
        else:
            filename = f"homepage_{url_hash}.html"

        # Sanitize filename
        filename = "".join(c if c.isalnum() or c in '-_.' else '_' for c in filename)

        return filename

    def fetch_page(self, url: str) -> Optional[Dict]:
        """
        Fetch a single page

        Args:
            url: URL to fetch

        Returns:
            Dict with HTML content and metadata, or None if failed
        """
        try:
            logger.info(f"Fetching: {url}")

            # Make request
            response = self.session.get(
                url,
                timeout=int(os.getenv('REQUEST_TIMEOUT_MS', 30000)) / 1000
            )

            # Check status
            response.raise_for_status()

            # Extract metadata
            result = {
                'url': url,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'html': response.text,
                'encoding': response.encoding,
                'timestamp': time.time(),
                'content_length': len(response.text)
            }

            logger.info(f"✓ Fetched {url} ({len(response.text)} bytes)")
            return result

        except requests.RequestException as e:
            logger.error(f"✗ Failed to fetch {url}: {e}")
            self.failed_urls.append({
                'url': url,
                'error': str(e),
                'timestamp': time.time()
            })
            return None

    def save_page(self, url: str, data: Dict) -> Path:
        """
        Save page HTML and metadata

        Args:
            url: Page URL
            data: Page data dict

        Returns:
            Path to saved HTML file
        """
        filename = self.generate_filename(url)
        html_path = self.output_dir / filename
        meta_path = self.output_dir / f"{filename}.meta.json"

        # Save HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(data['html'])

        # Save metadata
        metadata = {
            'url': data['url'],
            'status_code': data['status_code'],
            'timestamp': data['timestamp'],
            'content_length': data['content_length'],
            'encoding': data['encoding'],
            'filename': filename
        }

        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved to {html_path}")
        return html_path

    def extract_links(self, url: str, html: str) -> List[str]:
        """
        Extract valid links from HTML

        Args:
            url: Current page URL
            html: Page HTML

        Returns:
            List of absolute URLs
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']

            # Convert to absolute URL
            absolute_url = urljoin(url, href)

            # Normalize
            normalized = self.normalize_url(absolute_url)

            # Check if valid and not yet visited
            if (self.is_valid_url(normalized) and
                normalized not in self.visited_urls and
                normalized not in self.queued_urls):
                links.append(normalized)

        logger.info(f"Found {len(links)} new links on {url}")
        return links

    def crawl(self, start_urls: List[str]) -> Dict:
        """
        Crawl pages starting from seed URLs

        Args:
            start_urls: List of URLs to start crawling from

        Returns:
            Crawl statistics
        """
        # Initialize queue
        self.queued_urls = [self.normalize_url(url) for url in start_urls]

        pages_crawled = 0
        start_time = time.time()

        logger.info(f"Starting crawl with {len(self.queued_urls)} seed URLs")
        logger.info(f"Max pages: {self.max_pages}")

        while self.queued_urls and pages_crawled < self.max_pages:
            # Get next URL
            url = self.queued_urls.pop(0)

            # Skip if already visited
            if url in self.visited_urls:
                continue

            # Mark as visited
            self.visited_urls.add(url)

            # Fetch page
            page_data = self.fetch_page(url)

            if page_data:
                # Save page
                self.save_page(url, page_data)
                pages_crawled += 1

                # Extract and queue links
                if pages_crawled < self.max_pages:
                    new_links = self.extract_links(url, page_data['html'])
                    self.queued_urls.extend(new_links)

            # Respect crawl delay
            time.sleep(self.crawl_delay_ms / 1000)

        # Calculate statistics
        duration = time.time() - start_time

        stats = {
            'pages_crawled': pages_crawled,
            'pages_failed': len(self.failed_urls),
            'pages_queued': len(self.queued_urls),
            'duration_seconds': duration,
            'pages_per_second': pages_crawled / duration if duration > 0 else 0,
            'failed_urls': self.failed_urls
        }

        logger.info(f"Crawl complete: {pages_crawled} pages in {duration:.1f}s")

        return stats


def main():
    """Main entry point for crawler"""
    # Configuration from environment
    base_url = os.getenv('TARGET_URL', 'https://london.edu')
    max_pages = int(os.getenv('MAX_PAGES', 10))
    output_dir = os.getenv('RAW_HTML_DIR', './content-repo/raw')

    # Initial URLs to crawl
    start_urls = [
        f"{base_url}",
        f"{base_url}/about",
        f"{base_url}/programmes",
        f"{base_url}/faculty-and-research",
        f"{base_url}/news",
        f"{base_url}/events",
        f"{base_url}/admissions",
        f"{base_url}/student-life",
        f"{base_url}/alumni",
        f"{base_url}/contact"
    ]

    # Create crawler
    crawler = LBSCrawler(
        base_url=base_url,
        output_dir=output_dir,
        max_pages=max_pages
    )

    # Run crawl
    stats = crawler.crawl(start_urls)

    # Print results
    print("\n" + "="*60)
    print("CRAWL STATISTICS")
    print("="*60)
    print(f"Pages crawled:  {stats['pages_crawled']}")
    print(f"Pages failed:   {stats['pages_failed']}")
    print(f"Pages queued:   {stats['pages_queued']}")
    print(f"Duration:       {stats['duration_seconds']:.1f}s")
    print(f"Speed:          {stats['pages_per_second']:.2f} pages/s")
    print("="*60)

    if stats['failed_urls']:
        print("\nFailed URLs:")
        for failed in stats['failed_urls']:
            print(f"  - {failed['url']}: {failed['error']}")

    # Save stats
    stats_file = Path(output_dir) / 'crawl_stats.json'
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"\nStatistics saved to {stats_file}")


if __name__ == '__main__':
    main()
