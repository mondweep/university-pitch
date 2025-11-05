#!/usr/bin/env python3
"""
Parse script - Entry point for parsing HTML to JSON
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parser.html_parser import main

if __name__ == '__main__':
    main()
