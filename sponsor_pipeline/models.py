# Domain models for the HackCanada sponsor research pipeline.
# It defines all data classes and uses enumerations to maintain fixed set of values for each.

from __future__ import annotations
from enum import Enum

# Enumerations -----------------


class DiscoverySource(str, Enum):
    """
    Where a company was found during the discovery part of the pipeline.
    """

    MLH_EVENT = "mlh_event"
    HACKATHON_WEBSITE = "hackathon_website"
    DEVPOST = "devpost"
    JOB_POSTING = "job_posting"
    PRODUCT_LAUNCH = "product_launch"
    CANADIAN_RECRUITING = "canadian_recruiting"
    MANUAL_INPUT = "manual_input"


# ------------------------------


class LeadStatus(str, Enum):
    """
    Tracks where a company is in the pipeline at any given moment.
    """

    DISCOVERED = "discovered"
    SCORED = "scored"
    FILTERED_OUT = "filtered_out"
    RESEARCHED = "researched"
    CONTACTS_FOUND = "contacts_found"
    OUTREACH_READY = "outreach_ready"


# ------------------------------


class CompanySize(str, Enum):
    """
    Size classification used for scoring:
    - Too Small => low budget
    - Sweet Spot => best targets
    - Too Big => hard to reach
    """

    TOO_SMALL = "too_small"
    SWEET_SPOT = "sweet_spot"
    TOO_BIG = "too_big"
    UNKNOWN = "unknown"


# ------------------------------


class SponsorMotivation(str, Enum):
    """
    Why a company would want to be a sponsor (core of the scoring model)
    """

    HIRING_TALENT = "hiring_talent"
    DEVELOPER_ADOPTION = "developer_adoption"
    BRAND_COMMUNITY = "brand_community"


# ------------------------------


class ContactMethodType(str, Enum):
    """
    How to reach a contact person used by ContactDiscoveryService
    """

    EMAIL = "email"
    LINKEDIN = "linkedin"
    X_TWITTER = "x_twitter"
    GITHUB = "github"
    PERSONAL_WEBSITE = "personal_website"
    TEAM_PAGE = "team_page"
    BLOG_AUTHOR = "blog_author"
    CONFERENCE_SPEAKER = "conference_speaker"
    COMMUNITY_PAGE = "community_page"


# ------------------------------


class ContactRole(str, Enum):
    """
    The role of the person being contacted at a company
    """

    DEVREL = "devrel"
    DEV_ADVOCATE = "dev_advocate"
    COMMUNITY_MANAGER = "community_manager"
    DEV_MARKETING = "dev_marketing"
    CAMPUS_RECRUITER = "campus_recruiter"
    UNIVERSITY_RECRUITER = "university_recruiter"
    PARTNERSHIPS = "partnerships"
    FOUNDER_CEO = "founder_ceo"
    OTHER = "other"


# ------------------------------


class EvidenceCategory(str, Enum):
    """
    Categories of evidence when scoring a company and used by SponsorScoringService
    """

    PAST_SPONSORSHIP = "past_sponsorship"
    WATERLOO_CANADA_FIT = "waterloo_canada_fit"
    DEVELOPER_PRODUCT_FIT = "developer_product_fit"
    HIRING_SIGNAL = "hiring_signal"
    CONTACTABILITY = "contactability"


# ------------------------------


class SponsorTier(str, Enum):
    """
    Sponsorship package tier to pitch to a company
    """

    TITLE = "title"
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    IN_KIND = "in_kind"


# ------------------------------


class Priority(str, Enum):
    """
    Priority level assigned after scoring and filtering
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
