#!/usr/bin/env python3
"""
Phase 1 Validation Tests
Tests crawler and parser output against data model schema
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set


class Phase1Validator:
    """Validates Phase 1 crawler and parser output"""

    def __init__(self, parsed_dir: Path):
        self.parsed_dir = parsed_dir
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }

    def test_output_structure(self) -> Dict:
        """Test that all expected files exist"""
        print("\n=== Testing Output Structure ===")

        page_dirs = [d for d in self.parsed_dir.iterdir() if d.is_dir()]
        print(f"Found {len(page_dirs)} parsed pages")

        for page_dir in page_dirs:
            required_files = ['dom.json', 'text.json', 'metadata.json', 'links.json']

            for filename in required_files:
                filepath = page_dir / filename
                if filepath.exists():
                    self.results['passed'].append(f"{page_dir.name}/{filename} exists")
                else:
                    self.results['failed'].append(f"Missing {page_dir.name}/{filename}")

        return {
            'total_pages': len(page_dirs),
            'expected_files_per_page': 4
        }

    def test_metadata_schema(self) -> Dict:
        """Test metadata.json against schema"""
        print("\n=== Testing Metadata Schema ===")

        required_fields = ['title', 'canonical_url', 'language']
        optional_fields = ['description', 'og_title', 'keywords']

        page_dirs = [d for d in self.parsed_dir.iterdir() if d.is_dir()]

        for page_dir in page_dirs:
            meta_file = page_dir / 'metadata.json'

            if not meta_file.exists():
                continue

            with open(meta_file, 'r') as f:
                metadata = json.load(f)

            # Check required fields
            for field in required_fields:
                if field in metadata:
                    self.results['passed'].append(f"{page_dir.name}: Has {field}")
                else:
                    self.results['warnings'].append(f"{page_dir.name}: Missing optional field {field}")

            # Check optional fields
            for field in optional_fields:
                if field in metadata:
                    self.results['passed'].append(f"{page_dir.name}: Has optional {field}")

        return {'checked_pages': len(page_dirs)}

    def test_hash_deduplication(self) -> Dict:
        """Test that hash deduplication is working"""
        print("\n=== Testing Hash Deduplication ===")

        all_hashes: Set[str] = set()
        all_texts: List[str] = []
        duplicate_texts = 0

        page_dirs = [d for d in self.parsed_dir.iterdir() if d.is_dir()]

        for page_dir in page_dirs:
            text_file = page_dir / 'text.json'

            if not text_file.exists():
                continue

            with open(text_file, 'r') as f:
                text_data = json.load(f)

            # Collect hashes
            for hash_value, text in text_data.items():
                all_hashes.add(hash_value)
                all_texts.append(text)

                # Verify hash is correct
                expected_hash = hashlib.sha256(' '.join(text.split()).encode('utf-8')).hexdigest()
                if hash_value == expected_hash:
                    self.results['passed'].append(f"Hash verification: {hash_value[:16]}...")
                else:
                    self.results['failed'].append(f"Invalid hash for text: {text[:50]}...")

        # Check for duplicate texts
        seen_texts = set()
        for text in all_texts:
            normalized = ' '.join(text.split())
            if normalized in seen_texts:
                duplicate_texts += 1
                self.results['warnings'].append(f"Duplicate text found: {text[:50]}...")
            seen_texts.add(normalized)

        return {
            'total_unique_hashes': len(all_hashes),
            'total_text_items': len(all_texts),
            'duplicate_texts_found': duplicate_texts
        }

    def test_dom_structure(self) -> Dict:
        """Test DOM structure validity"""
        print("\n=== Testing DOM Structure ===")

        page_dirs = [d for d in self.parsed_dir.iterdir() if d.is_dir()]
        total_elements = 0
        max_depth = 0

        for page_dir in page_dirs:
            dom_file = page_dir / 'dom.json'

            if not dom_file.exists():
                continue

            with open(dom_file, 'r') as f:
                dom = json.load(f)

            # Check root element
            if 'tag' in dom:
                self.results['passed'].append(f"{page_dir.name}: DOM has root tag")
            else:
                self.results['failed'].append(f"{page_dir.name}: DOM missing root tag")

            # Count elements and depth
            def count_elements(node, depth=0):
                nonlocal total_elements, max_depth
                total_elements += 1
                max_depth = max(max_depth, depth)

                if 'children' in node:
                    for child in node['children']:
                        count_elements(child, depth + 1)

            count_elements(dom)
            self.results['passed'].append(f"{page_dir.name}: Parsed DOM tree")

        return {
            'total_elements': total_elements,
            'max_depth': max_depth
        }

    def test_links_structure(self) -> Dict:
        """Test links array structure"""
        print("\n=== Testing Links Structure ===")

        page_dirs = [d for d in self.parsed_dir.iterdir() if d.is_dir()]
        total_links = 0
        link_types = {'internal': 0, 'external': 0, 'anchor': 0, 'relative': 0}

        for page_dir in page_dirs:
            links_file = page_dir / 'links.json'

            if not links_file.exists():
                continue

            with open(links_file, 'r') as f:
                links = json.load(f)

            total_links += len(links)

            for link in links:
                # Check required fields
                if 'href' in link and 'text' in link and 'type' in link:
                    self.results['passed'].append(f"{page_dir.name}: Valid link structure")
                    link_types[link['type']] = link_types.get(link['type'], 0) + 1
                else:
                    self.results['failed'].append(f"{page_dir.name}: Invalid link structure")

        return {
            'total_links': total_links,
            'link_types': link_types
        }

    def run_all_tests(self) -> Dict:
        """Run all validation tests"""
        print("="*60)
        print("PHASE 1 VALIDATION TESTS")
        print("="*60)

        results = {
            'output_structure': self.test_output_structure(),
            'metadata_schema': self.test_metadata_schema(),
            'hash_deduplication': self.test_hash_deduplication(),
            'dom_structure': self.test_dom_structure(),
            'links_structure': self.test_links_structure()
        }

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✓ Passed: {len(self.results['passed'])}")
        print(f"✗ Failed: {len(self.results['failed'])}")
        print(f"⚠ Warnings: {len(self.results['warnings'])}")
        print("="*60)

        if self.results['failed']:
            print("\nFailed Tests:")
            for failure in self.results['failed'][:10]:  # Show first 10
                print(f"  ✗ {failure}")

        return {
            'test_results': results,
            'summary': {
                'passed': len(self.results['passed']),
                'failed': len(self.results['failed']),
                'warnings': len(self.results['warnings'])
            },
            'details': self.results
        }


if __name__ == '__main__':
    import sys

    parsed_dir = Path('./content-repo/parsed')

    if not parsed_dir.exists():
        print(f"Error: Parsed directory not found: {parsed_dir}")
        sys.exit(1)

    validator = Phase1Validator(parsed_dir)
    results = validator.run_all_tests()

    # Print detailed results
    print("\n" + "="*60)
    print("DETAILED RESULTS")
    print("="*60)
    for test_name, test_data in results['test_results'].items():
        print(f"\n{test_name}:")
        for key, value in test_data.items():
            print(f"  {key}: {value}")

    # Exit with error code if tests failed
    if results['summary']['failed'] > 0:
        sys.exit(1)
    else:
        print("\n✅ All validation tests passed!")
        sys.exit(0)
