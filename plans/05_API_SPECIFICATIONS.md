# API Specifications

## Overview

This document defines all API endpoints, request/response formats, authentication mechanisms, and usage examples for the LBS Semantic Knowledge Graph platform.

**Base URL:** `https://api.lbs-knowledge-graph.example.com/v1`

**API Version:** 1.0
**Protocol:** HTTPS only
**Format:** JSON
**Authentication:** JWT Bearer tokens

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Pages API](#2-pages-api)
3. [Sections API](#3-sections-api)
4. [Content API](#4-content-api)
5. [Topics API](#5-topics-api)
6. [Categories API](#6-categories-api)
7. [Personas API](#7-personas-api)
8. [Graph Query API](#8-graph-query-api)
9. [Search API](#9-search-api)
10. [Admin API](#10-admin-api)
11. [Analytics API](#11-analytics-api)
12. [Error Codes](#12-error-codes)

---

## 1. Authentication

### 1.1 Get Access Token

**Endpoint:** `POST /auth/token`

**Description:** Obtain a JWT access token

**Request:**
```json
{
  "username": "user@london.edu",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "def50200..."
}
```

### 1.2 Refresh Token

**Endpoint:** `POST /auth/refresh`

**Request:**
```json
{
  "refresh_token": "def50200..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### 1.3 Authorization Header

All authenticated requests must include:
```
Authorization: Bearer <access_token>
```

---

## 2. Pages API

### 2.1 List Pages

**Endpoint:** `GET /pages`

**Description:** Retrieve a paginated list of pages

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| type | string | No | all | Filter by page type |
| category | string | No | all | Filter by category |
| limit | integer | No | 20 | Results per page (max 100) |
| offset | integer | No | 0 | Number of results to skip |
| sort | string | No | updated_at | Sort field |
| order | string | No | desc | Sort order (asc/desc) |
| search | string | No | - | Search query |

**Example Request:**
```bash
GET /pages?type=program&limit=10&offset=0&sort=importance&order=desc
```

**Response:**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "url": "https://london.edu/programmes/mba",
      "title": "MBA Programme",
      "description": "London Business School's MBA is ranked #1 in Europe",
      "type": "program",
      "language": "en",
      "importance": 0.95,
      "updatedAt": "2025-11-01T10:30:00Z",
      "sections": 8,
      "inboundLinks": 45
    }
  ],
  "pagination": {
    "total": 250,
    "limit": 10,
    "offset": 0,
    "pages": 25
  }
}
```

### 2.2 Get Page by ID

**Endpoint:** `GET /pages/:id`

**Description:** Retrieve detailed information about a specific page

**Example Request:**
```bash
GET /pages/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://london.edu/programmes/mba",
  "title": "MBA Programme",
  "description": "London Business School's MBA is ranked #1 in Europe",
  "type": "program",
  "category": "programmes",
  "language": "en",
  "hash": "abc123...",
  "contentHash": "def456...",
  "version": 3,
  "createdAt": "2025-01-15T09:00:00Z",
  "updatedAt": "2025-11-01T10:30:00Z",
  "fetchedAt": "2025-11-01T02:00:00Z",
  "keywords": ["MBA", "business school", "masters", "finance"],
  "ogImage": "https://london.edu/images/mba-hero.jpg",
  "importance": 0.95,
  "depth": 2,
  "inboundLinks": 45,
  "outboundLinks": 12,
  "sections": [
    {
      "id": "section-1",
      "type": "hero",
      "heading": "London Business School MBA"
    }
  ],
  "links": [
    {
      "target": "page-2",
      "text": "Apply Now",
      "type": "callout"
    }
  ],
  "topics": [
    {
      "id": "topic-1",
      "name": "Finance",
      "confidence": 0.92
    }
  ]
}
```

### 2.3 Create Page

**Endpoint:** `POST /pages`

**Auth:** Required (Admin)

**Request:**
```json
{
  "url": "https://london.edu/new-page",
  "title": "New Page Title",
  "description": "Page description",
  "type": "other",
  "metadata": {
    "custom_field": "value"
  }
}
```

**Response:**
```json
{
  "id": "new-page-id",
  "url": "https://london.edu/new-page",
  "title": "New Page Title",
  "createdAt": "2025-11-01T12:00:00Z"
}
```

### 2.4 Update Page

**Endpoint:** `PUT /pages/:id`

**Auth:** Required (Admin)

**Request:**
```json
{
  "title": "Updated Title",
  "description": "Updated description"
}
```

**Response:**
```json
{
  "id": "page-id",
  "title": "Updated Title",
  "updatedAt": "2025-11-01T12:05:00Z"
}
```

### 2.5 Delete Page

**Endpoint:** `DELETE /pages/:id`

**Auth:** Required (Admin)

**Response:**
```json
{
  "success": true,
  "deletedAt": "2025-11-01T12:10:00Z"
}
```

---

## 3. Sections API

### 3.1 Get Section by ID

**Endpoint:** `GET /sections/:id`

**Response:**
```json
{
  "id": "section-id",
  "pageId": "page-id",
  "type": "content",
  "heading": "Section Heading",
  "order": 2,
  "contentItems": [
    {
      "id": "content-1",
      "text": "Content text...",
      "type": "paragraph"
    }
  ]
}
```

---

## 4. Content API

### 4.1 Get Content Item

**Endpoint:** `GET /content/:id`

**Response:**
```json
{
  "id": "content-id",
  "hash": "abc123...",
  "text": "London Business School offers world-class programmes...",
  "type": "paragraph",
  "sentiment": {
    "polarity": 0.8,
    "confidence": 0.9,
    "label": "positive"
  },
  "topics": ["mba", "education", "business"],
  "keywords": ["business school", "programmes", "education"],
  "entities": [
    {
      "text": "London Business School",
      "type": "organization",
      "confidence": 0.99
    }
  ],
  "audiences": ["prospective_student"],
  "usageCount": 3,
  "wordCount": 25,
  "language": "en"
}
```

### 4.2 Search Content

**Endpoint:** `GET /content/search`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Search query |
| topic | string | No | Filter by topic |
| sentiment | string | No | Filter by sentiment (positive/neutral/negative) |
| audience | string | No | Filter by audience |
| limit | integer | No | Results limit |

**Example:**
```bash
GET /content/search?q=finance&sentiment=positive&limit=10
```

**Response:**
```json
{
  "results": [
    {
      "id": "content-id",
      "text": "Finance programme ranked #1...",
      "score": 0.95,
      "highlights": ["<mark>Finance</mark> programme"]
    }
  ],
  "total": 42
}
```

---

## 5. Topics API

### 5.1 List Topics

**Endpoint:** `GET /topics`

**Query Parameters:**
- category (string)
- limit (integer)
- sort (string): name|contentCount|importance

**Response:**
```json
{
  "topics": [
    {
      "id": "topic-id",
      "name": "Finance",
      "slug": "finance",
      "category": "subjects",
      "description": "Financial management and investment",
      "contentCount": 150,
      "pageCount": 25,
      "importance": 0.9,
      "relatedTopics": ["topic-2", "topic-3"]
    }
  ],
  "total": 50
}
```

### 5.2 Get Topic

**Endpoint:** `GET /topics/:id`

**Response:**
```json
{
  "id": "topic-id",
  "name": "Finance",
  "slug": "finance",
  "category": "subjects",
  "level": 1,
  "description": "Financial management and investment",
  "aliases": ["Financial Management", "Corporate Finance"],
  "subtopics": [
    {
      "id": "subtopic-1",
      "name": "Investment Banking"
    }
  ],
  "contentCount": 150,
  "pageCount": 25,
  "importance": 0.9
}
```

### 5.3 Get Topic Content

**Endpoint:** `GET /topics/:id/content`

**Query Parameters:**
- limit (integer)
- offset (integer)
- type (string): page|section|content

**Response:**
```json
{
  "topic": {
    "id": "topic-id",
    "name": "Finance"
  },
  "content": [
    {
      "id": "content-id",
      "text": "Finance content...",
      "confidence": 0.92,
      "source": "llm"
    }
  ],
  "total": 150
}
```

---

## 6. Categories API

### 6.1 Get Category Tree

**Endpoint:** `GET /categories`

**Response:**
```json
{
  "categories": [
    {
      "id": "cat-1",
      "name": "Programmes",
      "slug": "programmes",
      "level": 0,
      "children": [
        {
          "id": "cat-2",
          "name": "MBA",
          "slug": "mba",
          "level": 1,
          "topicCount": 25,
          "pageCount": 15
        }
      ]
    }
  ]
}
```

---

## 7. Personas API

### 7.1 List Personas

**Endpoint:** `GET /personas`

**Response:**
```json
{
  "personas": [
    {
      "id": "persona-1",
      "name": "Prospective Student",
      "slug": "prospective-student",
      "type": "prospective_student",
      "description": "Individuals considering LBS programmes",
      "interests": ["mba", "admissions", "career"],
      "priority": 5,
      "contentCount": 350
    }
  ]
}
```

### 7.2 Get Persona Content

**Endpoint:** `GET /personas/:id/content`

**Response:**
```json
{
  "persona": {
    "id": "persona-1",
    "name": "Prospective Student"
  },
  "content": [
    {
      "id": "page-1",
      "type": "page",
      "title": "Admissions",
      "relevance": 0.95
    }
  ],
  "total": 350
}
```

---

## 8. Graph Query API

### 8.1 Execute Query

**Endpoint:** `POST /graph/query`

**Request:**
```json
{
  "query": "MATCH (p:Page)-[:LINKS_TO]->(target:Page {id: $targetId}) RETURN p",
  "params": {
    "targetId": "page-id"
  },
  "limit": 100
}
```

**Response:**
```json
{
  "results": [
    {
      "p": {
        "id": "page-1",
        "title": "Homepage",
        "url": "https://london.edu"
      }
    }
  ],
  "executionTime": 45,
  "count": 1
}
```

### 8.2 Traverse Graph

**Endpoint:** `GET /graph/traverse`

**Query Parameters:**
- start (string): Starting node ID
- depth (integer): Traversal depth (default: 1, max: 5)
- direction (string): outbound|inbound|both
- relationship (string): Optional relationship type filter

**Example:**
```bash
GET /graph/traverse?start=page-1&depth=2&direction=outbound&relationship=LINKS_TO
```

**Response:**
```json
{
  "start": {
    "id": "page-1",
    "title": "Homepage"
  },
  "paths": [
    {
      "nodes": [
        {"id": "page-1", "title": "Homepage"},
        {"id": "page-2", "title": "Programmes"},
        {"id": "page-3", "title": "MBA"}
      ],
      "relationships": [
        {"type": "LINKS_TO", "from": "page-1", "to": "page-2"},
        {"type": "LINKS_TO", "from": "page-2", "to": "page-3"}
      ]
    }
  ],
  "stats": {
    "nodesVisited": 15,
    "edgesTraversed": 20,
    "executionTime": 120
  }
}
```

### 8.3 Get Related Content

**Endpoint:** `GET /graph/related/:id`

**Query Parameters:**
- type (string): topic|link|semantic
- limit (integer)

**Response:**
```json
{
  "source": {
    "id": "page-1",
    "title": "MBA Programme"
  },
  "related": [
    {
      "id": "page-2",
      "title": "Executive MBA",
      "relationship": "topic",
      "score": 0.85
    }
  ]
}
```

---

## 9. Search API

### 9.1 Full-Text Search

**Endpoint:** `GET /search`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| q | string | Search query (required) |
| type | string | Filter by type (page/section/content) |
| topic | string | Filter by topic |
| category | string | Filter by category |
| sentiment | string | Filter by sentiment |
| audience | string | Filter by audience |
| limit | integer | Results limit (default: 20) |
| offset | integer | Pagination offset |
| highlight | boolean | Enable highlighting (default: true) |

**Example:**
```bash
GET /search?q=finance&topic=mba&sentiment=positive&limit=10
```

**Response:**
```json
{
  "query": "finance",
  "results": [
    {
      "id": "page-1",
      "type": "page",
      "title": "Finance Specialisation",
      "url": "https://london.edu/programmes/mba/specialisations/finance",
      "snippet": "Our <mark>finance</mark> specialisation provides comprehensive training...",
      "score": 0.95,
      "highlights": [
        "Our <mark>finance</mark> specialisation",
        "world-leading <mark>finance</mark> faculty"
      ],
      "topics": ["finance", "mba"],
      "sentiment": "positive"
    }
  ],
  "facets": {
    "type": {
      "page": 15,
      "content": 42
    },
    "topic": {
      "finance": 30,
      "investment": 12
    },
    "sentiment": {
      "positive": 45,
      "neutral": 10
    }
  },
  "suggestions": [
    "finance MBA",
    "finance courses",
    "finance faculty"
  ],
  "total": 57,
  "executionTime": 45
}
```

### 9.2 Autocomplete

**Endpoint:** `GET /search/autocomplete`

**Query Parameters:**
- q (string): Partial query
- limit (integer): Suggestions limit (default: 10)

**Example:**
```bash
GET /search/autocomplete?q=fin&limit=5
```

**Response:**
```json
{
  "suggestions": [
    "finance",
    "finance MBA",
    "financial management",
    "fintech",
    "finance faculty"
  ]
}
```

---

## 10. Admin API

### 10.1 Update Tags

**Endpoint:** `PUT /admin/nodes/:id/tags`

**Auth:** Required (Admin)

**Request:**
```json
{
  "tags": ["finance", "mba", "programme"]
}
```

**Response:**
```json
{
  "id": "node-id",
  "tags": ["finance", "mba", "programme"],
  "updatedAt": "2025-11-01T12:00:00Z"
}
```

### 10.2 Bulk Update

**Endpoint:** `POST /admin/bulk-update`

**Auth:** Required (Admin)

**Request:**
```json
{
  "nodeIds": ["node-1", "node-2", "node-3"],
  "updates": {
    "category": "programmes",
    "tags": ["add:finance", "remove:old-tag"]
  }
}
```

**Response:**
```json
{
  "updated": 3,
  "failed": 0,
  "errors": []
}
```

### 10.3 Quality Report

**Endpoint:** `GET /admin/quality-report`

**Auth:** Required (Admin)

**Response:**
```json
{
  "generatedAt": "2025-11-01T12:00:00Z",
  "summary": {
    "totalNodes": 5000,
    "totalEdges": 15000,
    "orphanedNodes": 12,
    "missingTags": 45,
    "brokenLinks": 3,
    "duplicateContent": 8
  },
  "issues": [
    {
      "type": "orphaned_node",
      "severity": "warning",
      "nodeId": "node-123",
      "message": "Node has no incoming or outgoing relationships"
    },
    {
      "type": "broken_link",
      "severity": "error",
      "sourceId": "page-1",
      "targetUrl": "https://london.edu/missing",
      "message": "Link target returns 404"
    }
  ],
  "recommendations": [
    {
      "type": "add_topic",
      "nodeId": "content-456",
      "suggestion": "Consider adding topic 'finance' (confidence: 0.85)"
    }
  ]
}
```

### 10.4 Trigger Pipeline

**Endpoint:** `POST /admin/pipeline/trigger`

**Auth:** Required (Admin)

**Request:**
```json
{
  "job": "crawler",
  "params": {
    "urls": ["https://london.edu/new-page"]
  }
}
```

**Response:**
```json
{
  "jobId": "job-123",
  "status": "queued",
  "queuedAt": "2025-11-01T12:00:00Z"
}
```

---

## 11. Analytics API

### 11.1 Get Statistics

**Endpoint:** `GET /analytics/stats`

**Response:**
```json
{
  "pages": {
    "total": 250,
    "byType": {
      "program": 45,
      "faculty": 80,
      "news": 60
    }
  },
  "content": {
    "totalItems": 5000,
    "totalWords": 250000,
    "uniqueSnippets": 3500
  },
  "graph": {
    "nodes": 5000,
    "edges": 15000,
    "avgDegree": 3.0
  },
  "topics": {
    "total": 50,
    "topTopics": [
      {"name": "Finance", "count": 150},
      {"name": "Leadership", "count": 120}
    ]
  }
}
```

### 11.2 Search Analytics

**Endpoint:** `GET /analytics/search`

**Query Parameters:**
- timeframe (string): 24h|7d|30d|90d

**Response:**
```json
{
  "timeframe": "7d",
  "totalSearches": 1250,
  "uniqueQueries": 450,
  "topQueries": [
    {"query": "MBA", "count": 85},
    {"query": "finance programme", "count": 62}
  ],
  "avgResultsReturned": 15.3,
  "avgExecutionTime": 120
}
```

---

## 12. Error Codes

### 12.1 HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### 12.2 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "url",
        "message": "URL must start with https://london.edu"
      }
    ],
    "requestId": "req-123",
    "timestamp": "2025-11-01T12:00:00Z"
  }
}
```

### 12.3 Common Error Codes

| Code | Description |
|------|-------------|
| AUTHENTICATION_REQUIRED | Missing authentication token |
| INVALID_TOKEN | Invalid or expired token |
| PERMISSION_DENIED | Insufficient permissions |
| RESOURCE_NOT_FOUND | Requested resource not found |
| VALIDATION_ERROR | Request validation failed |
| DUPLICATE_RESOURCE | Resource already exists |
| RATE_LIMIT_EXCEEDED | API rate limit exceeded |
| INTERNAL_ERROR | Internal server error |
| SERVICE_UNAVAILABLE | Service temporarily unavailable |

---

## 13. Rate Limiting

### 13.1 Rate Limits

| User Type | Requests/Hour | Requests/Day |
|-----------|---------------|--------------|
| Anonymous | 100 | 1,000 |
| Authenticated | 1,000 | 10,000 |
| Admin | 10,000 | 100,000 |

### 13.2 Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1635782400
```

---

## 14. Webhooks (Optional)

### 14.1 Register Webhook

**Endpoint:** `POST /webhooks`

**Request:**
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["page.updated", "content.created"],
  "secret": "webhook_secret"
}
```

### 14.2 Webhook Events

- `page.created`
- `page.updated`
- `page.deleted`
- `content.created`
- `content.updated`
- `topic.created`
- `graph.rebuilt`

---

**Document Version:** 1.0
**Last Updated:** November 2025
