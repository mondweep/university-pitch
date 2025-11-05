# LBS Website Taxonomy - Preliminary Analysis

## Document Information
- **Project:** London Business School Semantic Knowledge Graph
- **Phase:** Phase 1 Research
- **Created:** 2025-11-05
- **Purpose:** Preliminary taxonomy of london.edu content based on schema requirements and standard business school patterns

---

## Executive Summary

This document defines the preliminary taxonomy for London Business School's website content. The taxonomy will evolve based on actual crawled content but provides a starting framework for Phase 2 categorization and Phase 3 graph construction.

**Structure:** 3-level hierarchy (Root → Primary → Secondary categories) with cross-cutting topic tags and persona-based views.

---

## 1. Category Hierarchy

### Level 0: Root Categories

```
London Business School (Root)
├── 1. Programmes & Education
├── 2. Faculty & Research
├── 3. Admissions & Recruitment
├── 4. Student Experience
├── 5. Alumni & Community
├── 6. About & Governance
└── 7. News & Events
```

---

### Level 1-2: Detailed Taxonomy

#### 1. Programmes & Education

```
Programmes & Education
├── Degree Programmes
│   ├── MBA (Full-time)
│   ├── Executive MBA
│   ├── Masters in Finance
│   ├── Masters in Management
│   ├── Masters in Analytics & Management
│   ├── PhD Programme
│   └── Sloan Fellowship
├── Executive Education
│   ├── Open Programmes
│   ├── Custom Programmes
│   ├── Online Programmes
│   └── Coaching
├── Course Catalog
│   ├── Core Courses
│   ├── Electives
│   ├── Majors & Specialisations
│   └── Cross-Programme Courses
└── Academic Resources
    ├── Academic Calendar
    ├── Curriculum Structure
    ├── Teaching Methods
    └── Assessment & Grading
```

**Example URLs:**
- `/programmes/mba`
- `/programmes/masters-in-finance`
- `/executive-education/open-programmes`
- `/courses/strategy`

**Page Types:** `PageType.Program`, `PageType.Other`

---

#### 2. Faculty & Research

```
Faculty & Research
├── Faculty Profiles
│   ├── By Department
│   │   ├── Accounting
│   │   ├── Economics
│   │   ├── Finance
│   │   ├── Management Science & Operations
│   │   ├── Marketing
│   │   ├── Organisational Behaviour
│   │   └── Strategy & Entrepreneurship
│   ├── By Expertise Area
│   └── Visiting Faculty
├── Research Centres & Initiatives
│   ├── Centre for Corporate Governance
│   ├── Centre for Women in Business
│   ├── Private Equity Institute
│   ├── Wheeler Institute
│   └── Innovation & Entrepreneurship
├── Publications & Outputs
│   ├── Working Papers
│   ├── Books
│   ├── Case Studies
│   ├── London Business School Review
│   └── Research Blog
└── Research Impact
    ├── Industry Partnerships
    ├── Policy Influence
    └── Consulting Projects
```

**Example URLs:**
- `/faculty-and-research/faculty/john-doe`
- `/faculty-and-research/departments/finance`
- `/faculty-and-research/research-centres/corporate-governance`
- `/faculty-and-research/publications`

**Page Types:** `PageType.Faculty`, `PageType.Research`

---

#### 3. Admissions & Recruitment

```
Admissions & Recruitment
├── Application Process
│   ├── How to Apply
│   ├── Requirements
│   ├── Selection Criteria
│   ├── Deadlines
│   └── Application Portal
├── Financing Your Studies
│   ├── Tuition Fees
│   ├── Scholarships
│   ├── Loans & Financing
│   └── Financial Aid
├── Visit & Connect
│   ├── Campus Tours
│   ├── Information Sessions
│   ├── Webinars
│   ├── Meet Current Students
│   └── Admissions Team
└── Pre-Programme Resources
    ├── Pre-MBA Resources
    ├── Language Requirements
    └── Preparation Courses
```

**Example URLs:**
- `/admissions/mba/how-to-apply`
- `/admissions/scholarships`
- `/admissions/visit-campus`
- `/admissions/requirements`

**Page Types:** `PageType.Admissions`

---

#### 4. Student Experience

```
Student Experience
├── Campus Life
│   ├── London Campus
│   ├── Dubai Campus
│   ├── Facilities
│   ├── Library
│   └── Accommodation
├── Student Services
│   ├── Career Services
│   ├── Learning & Development
│   ├── Student Support
│   ├── Health & Wellbeing
│   └── International Students Office
├── Clubs & Activities
│   ├── Student Clubs
│   ├── Sports & Recreation
│   ├── Social Events
│   └── Student Leadership
├── Global Opportunities
│   ├── Exchange Programmes
│   ├── Global Immersions
│   ├── Study Tours
│   └── International Campuses
└── Careers & Recruiting
    ├── Career Development
    ├── Job Search Support
    ├── Employer Recruitment
    ├── Career Outcomes
    └── Industry Connections
```

**Example URLs:**
- `/student-life/campus`
- `/student-life/clubs`
- `/student-life/careers`
- `/student-life/facilities`

**Page Types:** `PageType.StudentLife`

---

#### 5. Alumni & Community

```
Alumni & Community
├── Alumni Network
│   ├── Alumni Directory
│   ├── Regional Chapters
│   ├── Alumni Groups
│   └── Mentoring Programme
├── Lifelong Learning
│   ├── Continuing Education
│   ├── Alumni Webinars
│   ├── Executive Programmes
│   └── Thought Leadership
├── Alumni Services
│   ├── Career Support
│   ├── Library Access
│   ├── Networking Events
│   └── Benefits & Discounts
└── Giving & Engagement
    ├── Ways to Give
    ├── Volunteer Opportunities
    ├── Fundraising Campaigns
    └── Impact Stories
```

**Example URLs:**
- `/alumni/network`
- `/alumni/events`
- `/alumni/giving`
- `/alumni/careers`

**Page Types:** `PageType.Alumni`

---

#### 6. About & Governance

```
About & Governance
├── About LBS
│   ├── Mission & Vision
│   ├── History
│   ├── Rankings & Accreditation
│   ├── Leadership Team
│   └── Facts & Figures
├── Governance
│   ├── Board of Governors
│   ├── Academic Council
│   ├── Policies & Procedures
│   └── Reports & Compliance
├── Partnerships
│   ├── Corporate Partners
│   ├── Academic Partners
│   ├── Global Alliance
│   └── Sponsorships
└── Contact & Locations
    ├── Contact Information
    ├── Campus Locations
    ├── Departments & Offices
    └── Maps & Directions
```

**Example URLs:**
- `/about/mission`
- `/about/leadership`
- `/about/rankings`
- `/contact`

**Page Types:** `PageType.About`, `PageType.Contact`

---

#### 7. News & Events

```
News & Events
├── News
│   ├── Press Releases
│   ├── Faculty Insights
│   ├── Student Stories
│   ├── Alumni Achievements
│   └── Research News
├── Events
│   ├── Academic Seminars
│   ├── Public Lectures
│   ├── Networking Events
│   ├── Career Fairs
│   └── Conferences
├── Media & Press
│   ├── Media Centre
│   ├── Press Contacts
│   ├── Brand Guidelines
│   └── Media Mentions
└── Thought Leadership
    ├── Blog
    ├── Podcasts
    ├── Videos
    └── Opinion Pieces
```

**Example URLs:**
- `/news/press-releases`
- `/news/faculty-insights`
- `/events/upcoming`
- `/events/seminars`

**Page Types:** `PageType.News`, `PageType.Event`

---

## 2. Topic Taxonomy

### Academic Disciplines

```
Business Disciplines
├── Accounting & Finance
│   ├── Corporate Finance
│   ├── Financial Markets
│   ├── Investment Management
│   ├── Accounting Standards
│   └── Risk Management
├── Economics
│   ├── Microeconomics
│   ├── Macroeconomics
│   ├── Econometrics
│   └── Behavioural Economics
├── Marketing
│   ├── Brand Management
│   ├── Digital Marketing
│   ├── Consumer Behaviour
│   ├── Marketing Analytics
│   └── Strategic Marketing
├── Strategy
│   ├── Corporate Strategy
│   ├── Competitive Strategy
│   ├── Business Models
│   └── Strategic Planning
├── Operations & Analytics
│   ├── Operations Management
│   ├── Supply Chain
│   ├── Data Analytics
│   ├── Decision Science
│   └── Business Intelligence
├── Organisational Behaviour
│   ├── Leadership
│   ├── Team Dynamics
│   ├── Change Management
│   ├── Organisational Culture
│   └── Negotiation
└── Entrepreneurship & Innovation
    ├── Startup Strategy
    ├── Venture Capital
    ├── Innovation Management
    ├── Corporate Entrepreneurship
    └── Social Entrepreneurship
```

### Cross-Cutting Themes

```
Themes
├── Sustainability & ESG
│   ├── Environmental Sustainability
│   ├── Social Impact
│   ├── Corporate Governance
│   └── Responsible Business
├── Technology & Digital
│   ├── Digital Transformation
│   ├── Artificial Intelligence
│   ├── Fintech
│   ├── E-commerce
│   └── Cybersecurity
├── Globalisation
│   ├── International Business
│   ├── Emerging Markets
│   ├── Cross-Cultural Management
│   └── Global Trade
├── Diversity & Inclusion
│   ├── Gender Diversity
│   ├── Inclusive Leadership
│   ├── Workplace Equity
│   └── Cultural Diversity
└── Future of Work
    ├── Remote Work
    ├── Gig Economy
    ├── Automation
    └── Workforce Development
```

**Implementation:** Topics will be extracted via LLM analysis in Phase 6 (Semantic Enrichment).

---

## 3. Persona-Based Taxonomy

### Primary Personas

#### Prospective Students

**Interests:**
- Programme information (curriculum, faculty, outcomes)
- Admissions process and requirements
- Student experience and campus life
- Career services and outcomes
- Financing and scholarships
- Rankings and reputation

**Content Preferences:**
- Programme pages
- Admissions guidance
- Student testimonials
- Career statistics
- Virtual tours
- Application tips

**Typical Journeys:**
1. Homepage → Programmes → MBA → Admissions → Apply
2. Homepage → News → Faculty Insights → Programmes
3. Rankings → Programme Comparison → Visit Campus

---

#### Current Students

**Interests:**
- Course catalog and schedules
- Career services
- Academic resources
- Student clubs and events
- Campus facilities
- Study abroad opportunities

**Content Preferences:**
- Student portal access
- Course listings
- Event calendar
- Career resources
- Club information
- Academic policies

**Typical Journeys:**
1. Student Portal → Course Catalog → Registration
2. Homepage → Events → Student Events
3. Career Services → Job Board → Employers

---

#### Alumni

**Interests:**
- Alumni network and events
- Continuing education
- Career support
- Giving opportunities
- Faculty research and insights
- Networking opportunities

**Content Preferences:**
- Alumni news
- Networking events
- Executive education
- Thought leadership
- Impact stories
- Regional chapters

**Typical Journeys:**
1. Alumni Portal → Events → Register
2. Homepage → Executive Education → Apply
3. News → Alumni Achievements → Network

---

#### Faculty & Researchers

**Interests:**
- Research centres and resources
- Publication opportunities
- Academic events and seminars
- Teaching resources
- Collaboration opportunities
- Grant funding

**Content Preferences:**
- Research publications
- Faculty profiles
- Academic seminars
- Research centres
- Collaboration tools
- Teaching materials

**Typical Journeys:**
1. Research → Publications → Submit
2. Faculty Profiles → Research Centres
3. Events → Academic Seminars

---

#### Corporate Partners

**Interests:**
- Recruiting opportunities
- Custom executive education
- Research partnerships
- Sponsorship opportunities
- Thought leadership
- Industry events

**Content Preferences:**
- Employer recruitment
- Custom programmes
- Research collaborations
- Partnership opportunities
- Industry insights
- Networking events

**Typical Journeys:**
1. Recruitment → Post Job → Meet Students
2. Executive Education → Custom Programmes → Enquire
3. Research → Industry Partnerships → Connect

---

#### Media & Press

**Interests:**
- Press releases
- Faculty expert commentary
- Research findings
- Rankings and statistics
- Institutional news
- Media resources

**Content Preferences:**
- Media centre
- Press releases
- Faculty expertise directory
- Research highlights
- Brand guidelines
- Media contacts

**Typical Journeys:**
1. Media Centre → Press Releases
2. Faculty Profiles → Expert Commentary
3. Research → Latest Findings

---

## 4. Content Categorisation Rules

### Automatic Classification

**URL Pattern Matching:**

```python
category_rules = {
    # Programmes & Education
    r'/programmes/': 'Programmes & Education',
    r'/executive-education/': 'Programmes & Education',
    r'/courses/': 'Programmes & Education',

    # Faculty & Research
    r'/faculty-and-research/': 'Faculty & Research',
    r'/research/': 'Faculty & Research',
    r'/departments/': 'Faculty & Research',

    # Admissions
    r'/admissions/': 'Admissions & Recruitment',
    r'/apply/': 'Admissions & Recruitment',
    r'/scholarships/': 'Admissions & Recruitment',

    # Student Experience
    r'/student-life/': 'Student Experience',
    r'/careers/': 'Student Experience',
    r'/campus/': 'Student Experience',

    # Alumni
    r'/alumni/': 'Alumni & Community',
    r'/giving/': 'Alumni & Community',

    # About
    r'/about/': 'About & Governance',
    r'/contact/': 'About & Governance',
    r'/governance/': 'About & Governance',

    # News & Events
    r'/news/': 'News & Events',
    r'/events/': 'News & Events',
    r'/insights/': 'News & Events'
}
```

**Content-Based Classification:**

```python
def classify_by_content(page: Page) -> str:
    """
    Fallback classification based on content

    Signals:
    1. Keywords in title
    2. Meta tags
    3. Breadcrumb structure
    4. Dominant topics in text
    """
    title_lower = page.title.lower()

    # Programme keywords
    if any(kw in title_lower for kw in ['mba', 'masters', 'phd', 'programme']):
        return 'Programmes & Education'

    # Faculty keywords
    if any(kw in title_lower for kw in ['professor', 'faculty', 'research']):
        return 'Faculty & Research'

    # ... additional rules
```

---

## 5. Metadata Mapping

### Category Entity Schema

```typescript
interface Category {
  id: string;
  name: string;
  slug: string;
  level: number;                // 0 = root, 1 = primary, 2 = secondary
  parentId?: string;
  children: string[];
  path: string[];               // Full path from root
  description?: string;
  icon?: string;
  color?: string;
  order: number;
  topicCount: number;
  pageCount: number;
  metadata: {
    keywords: string[];         // SEO keywords
    relatedCategories: string[]; // Related category IDs
    targetPersonas: string[];   // Primary personas
  };
}
```

### Example Category Instances

**Root Category:**
```json
{
  "id": "cat-001",
  "name": "Programmes & Education",
  "slug": "programmes-education",
  "level": 0,
  "parentId": null,
  "children": ["cat-002", "cat-003", "cat-004", "cat-005"],
  "path": ["cat-001"],
  "description": "Degree programmes, executive education, and academic resources",
  "icon": "graduation-cap",
  "color": "#003366",
  "order": 1,
  "topicCount": 45,
  "pageCount": 120,
  "metadata": {
    "keywords": ["MBA", "Masters", "PhD", "Executive Education"],
    "relatedCategories": ["cat-020"],
    "targetPersonas": ["prospective_student", "current_student"]
  }
}
```

**Primary Category:**
```json
{
  "id": "cat-002",
  "name": "Degree Programmes",
  "slug": "degree-programmes",
  "level": 1,
  "parentId": "cat-001",
  "children": ["cat-010", "cat-011", "cat-012"],
  "path": ["cat-001", "cat-002"],
  "description": "Full-time and part-time degree programmes",
  "icon": "book",
  "color": "#003366",
  "order": 1,
  "topicCount": 25,
  "pageCount": 40,
  "metadata": {
    "keywords": ["MBA", "Masters", "PhD"],
    "relatedCategories": ["cat-020", "cat-030"],
    "targetPersonas": ["prospective_student"]
  }
}
```

**Secondary Category:**
```json
{
  "id": "cat-010",
  "name": "MBA (Full-time)",
  "slug": "mba",
  "level": 2,
  "parentId": "cat-002",
  "children": [],
  "path": ["cat-001", "cat-002", "cat-010"],
  "description": "Full-time MBA programme",
  "icon": "briefcase",
  "color": "#003366",
  "order": 1,
  "topicCount": 8,
  "pageCount": 15,
  "metadata": {
    "keywords": ["MBA", "Full-time", "Business School"],
    "relatedCategories": ["cat-011", "cat-020"],
    "targetPersonas": ["prospective_student"]
  }
}
```

---

## 6. Implementation Roadmap

### Phase 2: Initial Taxonomy (Week 4)

**Actions:**
1. Create Category entities for Level 0-1 (Root + Primary)
2. Map crawled pages to categories via URL patterns
3. Validate category assignments (manual review)
4. Adjust taxonomy based on actual content

**Deliverables:**
- `categories.json` - Category entity definitions
- `page_categories.json` - Page-to-category mappings
- `taxonomy_validation.md` - Manual review report

---

### Phase 3: Topic Extraction (Week 5-6)

**Actions:**
1. Extract topics from content using LLM
2. Create Topic entities
3. Map topics to categories
4. Build topic hierarchy

**Deliverables:**
- `topics.json` - Topic entity definitions
- `topic_hierarchy.json` - Topic parent-child relationships
- `content_topics.json` - Content-to-topic mappings

---

### Phase 6: Persona Classification (Week 13-15)

**Actions:**
1. Create Persona entities
2. Classify content by target persona
3. Build persona-to-content mappings
4. Validate persona assignments

**Deliverables:**
- `personas.json` - Persona entity definitions
- `content_personas.json` - Content-to-persona mappings
- `persona_journeys.json` - Typical user journeys

---

## 7. Validation & Refinement

### Quality Metrics

**Category Coverage:**
- [ ] 100% of pages assigned to at least one category
- [ ] 95%+ of pages assigned to correct primary category
- [ ] 80%+ of pages assigned to secondary category

**Taxonomy Depth:**
- [ ] All categories have clear parent-child relationships
- [ ] No orphaned categories
- [ ] Maximum depth of 3 levels

**Consistency:**
- [ ] Category names follow consistent naming convention
- [ ] Slugs are URL-safe and unique
- [ ] Metadata complete for all categories

### Refinement Process

1. **Initial Assignment:** Automated via URL patterns
2. **Manual Review:** Validate 20% sample of pages
3. **Error Analysis:** Identify misclassifications
4. **Rule Refinement:** Update classification rules
5. **Re-classification:** Re-run on full dataset
6. **Final Validation:** Manual review of edge cases

---

## Appendices

### A. Complete Category List (Level 0-2)

```
1. Programmes & Education
   1.1 Degree Programmes
       1.1.1 MBA
       1.1.2 Executive MBA
       1.1.3 Masters in Finance
       1.1.4 Masters in Management
       1.1.5 Masters in Analytics
       1.1.6 PhD Programme
       1.1.7 Sloan Fellowship
   1.2 Executive Education
       1.2.1 Open Programmes
       1.2.2 Custom Programmes
       1.2.3 Online Programmes
   1.3 Course Catalog
   1.4 Academic Resources

2. Faculty & Research
   2.1 Faculty Profiles
       2.1.1 By Department
       2.1.2 By Expertise
   2.2 Research Centres
   2.3 Publications
   2.4 Research Impact

3. Admissions & Recruitment
   3.1 Application Process
   3.2 Financing
   3.3 Visit & Connect
   3.4 Pre-Programme Resources

4. Student Experience
   4.1 Campus Life
   4.2 Student Services
   4.3 Clubs & Activities
   4.4 Global Opportunities
   4.5 Careers

5. Alumni & Community
   5.1 Alumni Network
   5.2 Lifelong Learning
   5.3 Alumni Services
   5.4 Giving & Engagement

6. About & Governance
   6.1 About LBS
   6.2 Governance
   6.3 Partnerships
   6.4 Contact & Locations

7. News & Events
   7.1 News
   7.2 Events
   7.3 Media & Press
   7.4 Thought Leadership
```

### B. Reference Documents

- **Schema:** `/workspaces/university-pitch/plans/04_DATA_MODEL_SCHEMA.md`
- **Content Analysis:** `./CONTENT_ANALYSIS.md`
- **Domain Model:** `./DOMAIN_MODEL_RECOMMENDATIONS.md`

---

**Document Version:** 1.0
**Status:** Preliminary (Pre-Crawl)
**Next Update:** After Phase 2 Week 4 (post-crawl refinement)
