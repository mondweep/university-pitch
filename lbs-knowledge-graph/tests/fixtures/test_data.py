"""
Additional test data and fixtures for Phase 2 tests
"""

import hashlib
from typing import Dict, List, Any


# ==================== Page Type Classification Data ====================

PROGRAMME_PAGE_INDICATORS = {
    'urls': [
        'https://london.edu/programmes/mba',
        'https://london.edu/programmes/masters',
        'https://london.edu/programmes/phd',
        'https://london.edu/executive-education/emba'
    ],
    'titles': [
        'MBA Programme',
        'Masters in Finance',
        'PhD Programme',
        'Executive MBA'
    ],
    'keywords': ['programme', 'mba', 'masters', 'phd', 'course', 'degree']
}

FACULTY_PAGE_INDICATORS = {
    'urls': [
        'https://london.edu/faculty/john-doe',
        'https://london.edu/faculty-and-research/faculty/jane-smith'
    ],
    'titles': [
        'Professor John Doe',
        'Dr. Jane Smith - Faculty Profile'
    ],
    'keywords': ['professor', 'faculty', 'lecturer', 'researcher', 'dr', 'phd']
}

NEWS_PAGE_INDICATORS = {
    'urls': [
        'https://london.edu/news/2024/digital-transformation',
        'https://london.edu/news-and-insights/thought-leadership'
    ],
    'titles': [
        'Digital Transformation in Business',
        'New Research on Leadership'
    ],
    'keywords': ['news', 'article', 'press release', 'announcement', 'research']
}


# ==================== Section Type Data ====================

SECTION_TYPE_SAMPLES = {
    'hero': {
        'classes': ['hero', 'banner', 'hero-section', 'jumbotron'],
        'structure': ['h1', 'p', 'button'],
        'position': 'first'
    },
    'content': {
        'classes': ['content', 'main-content', 'article-content'],
        'structure': ['h2', 'p', 'ul', 'img'],
        'position': 'middle'
    },
    'sidebar': {
        'classes': ['sidebar', 'aside', 'related-content'],
        'structure': ['h3', 'ul', 'a'],
        'position': 'any'
    },
    'navigation': {
        'classes': ['nav', 'navigation', 'menu', 'navbar'],
        'structure': ['ul', 'li', 'a'],
        'position': 'first'
    },
    'footer': {
        'classes': ['footer', 'page-footer', 'site-footer'],
        'structure': ['p', 'a', 'ul'],
        'position': 'last'
    },
    'callout': {
        'classes': ['callout', 'cta', 'highlight', 'promo'],
        'structure': ['h3', 'p', 'button'],
        'position': 'any'
    },
    'listing': {
        'classes': ['listing', 'grid', 'card-list', 'items'],
        'structure': ['article', 'h3', 'p'],
        'position': 'middle'
    },
    'profile': {
        'classes': ['profile', 'bio', 'about', 'faculty-profile'],
        'structure': ['img', 'h2', 'p', 'ul'],
        'position': 'top'
    }
}


# ==================== Content Type Samples ====================

CONTENT_TYPE_SAMPLES = {
    'paragraph': [
        'This is a standard paragraph with multiple sentences. It contains narrative content.',
        'London Business School offers world-class programmes in business education.'
    ],
    'heading': [
        'Programme Overview',
        'Admissions Requirements',
        'About London Business School'
    ],
    'list': [
        ['First item', 'Second item', 'Third item'],
        ['MBA Programme', 'Masters Programmes', 'PhD Programme']
    ],
    'quote': [
        '"Leadership is about making others better as a result of your presence." - Professor John Doe',
        '"The best way to predict the future is to create it."'
    ]
}


# ==================== Complex DOM Structures ====================

NESTED_SECTIONS_DOM = {
    'tag': 'section',
    'attrs': {'class': 'parent-section'},
    'children': [
        {'tag': 'h2', 'text': 'Parent Section'},
        {
            'tag': 'section',
            'attrs': {'class': 'child-section-1'},
            'children': [
                {'tag': 'h3', 'text': 'Child Section 1'},
                {'tag': 'p', 'text': 'Content for child 1'}
            ]
        },
        {
            'tag': 'section',
            'attrs': {'class': 'child-section-2'},
            'children': [
                {'tag': 'h3', 'text': 'Child Section 2'},
                {
                    'tag': 'section',
                    'attrs': {'class': 'grandchild-section'},
                    'children': [
                        {'tag': 'h4', 'text': 'Grandchild Section'},
                        {'tag': 'p', 'text': 'Deeply nested content'}
                    ]
                }
            ]
        }
    ]
}


COMPLEX_LIST_DOM = {
    'tag': 'section',
    'children': [
        {
            'tag': 'ul',
            'attrs': {'class': 'main-list'},
            'children': [
                {
                    'tag': 'li',
                    'children': [
                        {'tag': 'strong', 'text': 'Item 1:'},
                        {'text': ' Description of item 1'}
                    ]
                },
                {
                    'tag': 'li',
                    'children': [
                        {'tag': 'strong', 'text': 'Item 2:'},
                        {'text': ' Description with '},
                        {'tag': 'a', 'attrs': {'href': '/link'}, 'text': 'link'},
                        {'text': ' included'}
                    ]
                },
                {
                    'tag': 'li',
                    'children': [
                        {'tag': 'strong', 'text': 'Item 3:'},
                        {
                            'tag': 'ul',
                            'children': [
                                {'tag': 'li', 'text': 'Nested item 1'},
                                {'tag': 'li', 'text': 'Nested item 2'}
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}


MEDIA_RICH_DOM = {
    'tag': 'section',
    'attrs': {'class': 'gallery'},
    'children': [
        {
            'tag': 'img',
            'attrs': {
                'src': '/images/campus.jpg',
                'alt': 'LBS Campus',
                'width': '800',
                'height': '600'
            }
        },
        {
            'tag': 'figure',
            'children': [
                {
                    'tag': 'img',
                    'attrs': {'src': '/images/lecture.jpg', 'alt': 'Lecture Hall'}
                },
                {
                    'tag': 'figcaption',
                    'text': 'State-of-the-art lecture facilities'
                }
            ]
        },
        {
            'tag': 'video',
            'attrs': {
                'src': '/videos/tour.mp4',
                'controls': 'true'
            }
        }
    ]
}


# ==================== Link Relationship Data ====================

INTERNAL_LINK_SAMPLES = [
    {
        'href': '/programmes/mba',
        'text': 'MBA Programme',
        'type': 'navigation',
        'context': 'main menu'
    },
    {
        'href': '/admissions',
        'text': 'Apply now',
        'type': 'internal',
        'context': 'call to action'
    },
    {
        'href': '/faculty/john-doe',
        'text': 'Professor John Doe',
        'type': 'reference',
        'context': 'faculty mention in article'
    }
]

EXTERNAL_LINK_SAMPLES = [
    {
        'href': 'https://example.com/research',
        'text': 'External Research',
        'type': 'external',
        'context': 'research citation'
    },
    {
        'href': 'https://linkedin.com/school/lbs',
        'text': 'Follow us on LinkedIn',
        'type': 'external',
        'context': 'social media'
    }
]


# ==================== Performance Test Data ====================

def generate_large_page(num_sections: int = 100) -> Dict[str, Any]:
    """Generate a large page for performance testing"""
    sections = []
    for i in range(num_sections):
        sections.append({
            'tag': 'section',
            'attrs': {'class': f'section-{i}', 'id': f'sec-{i}'},
            'children': [
                {'tag': 'h2', 'text': f'Section {i} Heading'},
                {'tag': 'p', 'text': f'This is paragraph content for section {i}. ' * 10},
                {
                    'tag': 'ul',
                    'children': [
                        {'tag': 'li', 'text': f'Item {j} in section {i}'}
                        for j in range(5)
                    ]
                }
            ]
        })

    return {
        'url': 'https://london.edu/large-page',
        'metadata': {
            'title': 'Large Test Page',
            'canonical_url': 'https://london.edu/large-page',
            'language': 'en'
        },
        'dom': {
            'tag': 'html',
            'children': [
                {
                    'tag': 'body',
                    'children': [
                        {
                            'tag': 'main',
                            'children': sections
                        }
                    ]
                }
            ]
        },
        'links': [
            {'href': f'/link-{i}', 'text': f'Link {i}', 'type': 'internal'}
            for i in range(50)
        ]
    }


def generate_test_pages(count: int) -> List[Dict[str, Any]]:
    """Generate multiple test pages"""
    pages = []
    page_types = ['program', 'faculty', 'news', 'event', 'about']

    for i in range(count):
        page_type = page_types[i % len(page_types)]
        pages.append({
            'url': f'https://london.edu/test-{i}',
            'metadata': {
                'title': f'Test Page {i} - {page_type}',
                'canonical_url': f'https://london.edu/test-{i}',
                'language': 'en'
            },
            'dom': {
                'tag': 'html',
                'children': [
                    {
                        'tag': 'body',
                        'children': [
                            {
                                'tag': 'main',
                                'children': [
                                    {'tag': 'h1', 'text': f'Page {i}'},
                                    {'tag': 'p', 'text': f'Content for test page {i}'}
                                ]
                            }
                        ]
                    }
                ]
            },
            'links': []
        })

    return pages


# ==================== Edge Cases ====================

EDGE_CASE_PAGES = {
    'empty_dom': {
        'url': 'https://london.edu/empty',
        'metadata': {'title': 'Empty', 'canonical_url': 'https://london.edu/empty', 'language': 'en'},
        'dom': {'tag': 'html', 'children': []},
        'links': []
    },
    'no_metadata': {
        'url': 'https://london.edu/no-meta',
        'metadata': {},
        'dom': {'tag': 'html', 'children': [{'tag': 'body', 'children': []}]},
        'links': []
    },
    'malformed_dom': {
        'url': 'https://london.edu/malformed',
        'metadata': {'title': 'Malformed', 'canonical_url': 'https://london.edu/malformed', 'language': 'en'},
        'dom': {'tag': 'div', 'children': []},  # Not html root
        'links': []
    },
    'circular_links': {
        'url': 'https://london.edu/circular',
        'metadata': {'title': 'Circular', 'canonical_url': 'https://london.edu/circular', 'language': 'en'},
        'dom': {'tag': 'html', 'children': []},
        'links': [
            {'href': '/page-a', 'text': 'A', 'type': 'internal'},
            {'href': '/page-b', 'text': 'B', 'type': 'internal'},
            {'href': '/circular', 'text': 'Self', 'type': 'internal'}  # Self-reference
        ]
    }
}
