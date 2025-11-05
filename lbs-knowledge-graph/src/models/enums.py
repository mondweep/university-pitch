"""
Enumeration types for the LBS Knowledge Graph domain model.

This module defines all enumeration types used across the domain entities,
ensuring type safety and consistency in entity classification.
"""

from enum import Enum


class PageType(str, Enum):
    """Classification of page types on london.edu"""

    HOMEPAGE = "homepage"
    PROGRAM = "program"
    FACULTY = "faculty"
    RESEARCH = "research"
    NEWS = "news"
    EVENT = "event"
    ABOUT = "about"
    ADMISSIONS = "admissions"
    STUDENT_LIFE = "student_life"
    ALUMNI = "alumni"
    CONTACT = "contact"
    OTHER = "other"


class SectionType(str, Enum):
    """Classification of section types within a page"""

    HERO = "hero"
    CONTENT = "content"
    SIDEBAR = "sidebar"
    NAVIGATION = "navigation"
    FOOTER = "footer"
    HEADER = "header"
    CALLOUT = "callout"
    LISTING = "listing"
    PROFILE = "profile"
    STATS = "stats"
    TESTIMONIAL = "testimonial"
    GALLERY = "gallery"
    FORM = "form"
    OTHER = "other"


class ContentType(str, Enum):
    """Classification of content item types"""

    PARAGRAPH = "paragraph"
    HEADING = "heading"
    SUBHEADING = "subheading"
    LIST = "list"
    LIST_ITEM = "list_item"
    QUOTE = "quote"
    CODE = "code"
    TABLE = "table"
    IMAGE = "image"
    VIDEO = "video"
    LINK = "link"
    BUTTON = "button"
    OTHER = "other"


class LinkType(str, Enum):
    """Classification of hyperlink types"""

    NAVIGATION = "navigation"
    INTERNAL = "internal"
    REFERENCE = "reference"
    RELATED = "related"
    EXTERNAL = "external"


class EntityType(str, Enum):
    """Classification of named entities"""

    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    PROGRAM = "program"
    COURSE = "course"
    DEPARTMENT = "department"
    OTHER = "other"
