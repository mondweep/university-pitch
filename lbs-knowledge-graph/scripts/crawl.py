#!/usr/bin/env python3
"""
Crawl script - Entry point for crawling london.edu
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from crawler.crawler import main

if __name__ == '__main__':
    main()
