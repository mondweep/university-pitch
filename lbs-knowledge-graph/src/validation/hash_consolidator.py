#!/usr/bin/env python3
"""
Hash Consolidator - Identify duplicate content across pages
Analyzes text hashes to detect content reuse and deduplication effectiveness
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import argparse


class HashConsolidator:
    """Consolidate and analyze text hashes across all parsed pages"""

    def __init__(self, data_dir: str = "data/parsed"):
        self.data_dir = Path(data_dir)
        self.hash_to_text: Dict[str, str] = {}
        self.hash_to_pages: Dict[str, Set[str]] = defaultdict(set)
        self.hash_to_sections: Dict[str, Set[str]] = defaultdict(set)
        self.hash_usage_count: Dict[str, int] = defaultdict(int)

    def load_page_data(self, page_file: Path) -> Dict:
        """Load and parse a single page JSON file"""
        with open(page_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_hashes(self, page_data: Dict, page_url: str) -> None:
        """Extract all text hashes from a page"""
        page_id = page_data.get('id', page_url)

        # Process sections
        sections = page_data.get('sections', [])
        for section in sections:
            section_id = section.get('id', f"{page_id}_section_{section.get('order', 0)}")

            # Process content items
            content_items = section.get('contentItems', [])
            for item in content_items:
                text_hash = item.get('hash')
                text = item.get('text', '')

                if text_hash and text:
                    # Store mapping
                    self.hash_to_text[text_hash] = text
                    self.hash_to_pages[text_hash].add(page_id)
                    self.hash_to_sections[text_hash].add(section_id)
                    self.hash_usage_count[text_hash] += 1

    def consolidate_all_pages(self) -> None:
        """Process all page files and consolidate hashes"""
        page_files = list(self.data_dir.glob('**/*.json'))

        print(f"Processing {len(page_files)} page files...")

        for i, page_file in enumerate(page_files, 1):
            try:
                page_data = self.load_page_data(page_file)
                page_url = page_data.get('url', str(page_file))
                self.extract_hashes(page_data, page_url)

                if i % 100 == 0:
                    print(f"  Processed {i}/{len(page_files)} pages...")
            except Exception as e:
                print(f"  Error processing {page_file}: {e}")

        print(f"✓ Consolidation complete!")
        print(f"  Total unique hashes: {len(self.hash_to_text)}")
        print(f"  Total hash occurrences: {sum(self.hash_usage_count.values())}")

    def find_duplicates(self, min_usage: int = 2) -> List[Dict]:
        """Find content that appears in multiple locations"""
        duplicates = []

        for text_hash, count in self.hash_usage_count.items():
            if count >= min_usage:
                duplicates.append({
                    'hash': text_hash,
                    'text': self.hash_to_text[text_hash][:200],  # First 200 chars
                    'text_length': len(self.hash_to_text[text_hash]),
                    'usage_count': count,
                    'pages': list(self.hash_to_pages[text_hash]),
                    'sections': list(self.hash_to_sections[text_hash])
                })

        # Sort by usage count (most duplicated first)
        duplicates.sort(key=lambda x: x['usage_count'], reverse=True)

        return duplicates

    def calculate_deduplication_rate(self) -> Dict[str, float]:
        """Calculate deduplication effectiveness metrics"""
        total_occurrences = sum(self.hash_usage_count.values())
        unique_hashes = len(self.hash_to_text)

        if total_occurrences == 0:
            return {
                'total_occurrences': 0,
                'unique_content_items': 0,
                'deduplication_rate': 0.0,
                'average_reuse': 0.0
            }

        deduplication_rate = (total_occurrences - unique_hashes) / total_occurrences
        average_reuse = total_occurrences / unique_hashes if unique_hashes > 0 else 0

        return {
            'total_occurrences': total_occurrences,
            'unique_content_items': unique_hashes,
            'deduplication_rate': round(deduplication_rate * 100, 2),  # Percentage
            'average_reuse': round(average_reuse, 2),
            'duplicate_items': sum(1 for count in self.hash_usage_count.values() if count > 1),
            'max_reuse': max(self.hash_usage_count.values()) if self.hash_usage_count else 0
        }

    def generate_hash_distribution(self) -> Dict[str, int]:
        """Generate distribution of hash usage counts"""
        distribution = defaultdict(int)

        for count in self.hash_usage_count.values():
            distribution[f"{count}x"] += 1

        return dict(sorted(distribution.items(), key=lambda x: int(x[0].replace('x', ''))))

    def export_consolidated_hashes(self, output_file: str = "data/consolidated_hashes.json") -> None:
        """Export consolidated hash data to JSON"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        consolidated_data = {
            'version': '1.0',
            'generated_at': str(Path.ctime(Path.cwd())),
            'statistics': {
                'total_unique_hashes': len(self.hash_to_text),
                'total_occurrences': sum(self.hash_usage_count.values()),
                'deduplication_metrics': self.calculate_deduplication_rate(),
                'usage_distribution': self.generate_hash_distribution()
            },
            'hashes': {
                text_hash: {
                    'text': text,
                    'usage_count': self.hash_usage_count[text_hash],
                    'pages': list(self.hash_to_pages[text_hash]),
                    'word_count': len(text.split())
                }
                for text_hash, text in self.hash_to_text.items()
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(consolidated_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Consolidated hashes exported to {output_path}")

    def print_summary(self) -> None:
        """Print summary statistics"""
        metrics = self.calculate_deduplication_rate()
        distribution = self.generate_hash_distribution()

        print("\n" + "="*60)
        print("HASH CONSOLIDATION SUMMARY")
        print("="*60)
        print(f"Total unique content items: {metrics['unique_content_items']:,}")
        print(f"Total content occurrences: {metrics['total_occurrences']:,}")
        print(f"Deduplication rate: {metrics['deduplication_rate']}%")
        print(f"Average content reuse: {metrics['average_reuse']}x")
        print(f"Items used multiple times: {metrics['duplicate_items']:,}")
        print(f"Maximum reuse count: {metrics['max_reuse']}x")

        print("\nUsage Distribution:")
        for usage, count in list(distribution.items())[:10]:  # Top 10
            print(f"  {usage:>6}: {count:>6,} items")

        if len(distribution) > 10:
            print(f"  ... and {len(distribution) - 10} more usage levels")

        print("="*60)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Consolidate text hashes across all parsed pages'
    )
    parser.add_argument(
        '--data-dir',
        default='data/parsed',
        help='Directory containing parsed page JSON files'
    )
    parser.add_argument(
        '--output',
        default='data/consolidated_hashes.json',
        help='Output file for consolidated hash data'
    )
    parser.add_argument(
        '--find-duplicates',
        action='store_true',
        help='Generate report of duplicate content'
    )
    parser.add_argument(
        '--min-usage',
        type=int,
        default=2,
        help='Minimum usage count for duplicate detection'
    )

    args = parser.parse_args()

    # Initialize consolidator
    consolidator = HashConsolidator(args.data_dir)

    # Process all pages
    consolidator.consolidate_all_pages()

    # Print summary
    consolidator.print_summary()

    # Export consolidated data
    consolidator.export_consolidated_hashes(args.output)

    # Find duplicates if requested
    if args.find_duplicates:
        print("\nFinding duplicate content...")
        duplicates = consolidator.find_duplicates(args.min_usage)

        print(f"\nFound {len(duplicates)} content items used {args.min_usage}+ times:")
        print("-" * 60)

        for i, dup in enumerate(duplicates[:20], 1):  # Show top 20
            print(f"\n{i}. [{dup['usage_count']}x] {dup['text'][:100]}...")
            print(f"   Pages: {len(dup['pages'])}, Sections: {len(dup['sections'])}")

        if len(duplicates) > 20:
            print(f"\n... and {len(duplicates) - 20} more duplicates")

    print("\n✓ Hash consolidation complete!")


if __name__ == "__main__":
    main()
