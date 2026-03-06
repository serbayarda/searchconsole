from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum


class SearchAnalyticsRow(BaseModel):
    query: str
    page: str
    clicks: int
    impressions: int
    ctr: float
    position: float


class KeywordOpportunity(BaseModel):
    query: str
    page: str
    clicks: int
    impressions: int
    ctr: float
    position: float
    expected_ctr: float
    ctr_gap: float
    opportunity_score: float
    search_intent: Optional[str] = None
    search_volume: Optional[int] = None


class SerpResult(BaseModel):
    rank: int
    url: str
    domain: str
    title: str
    description: str


class PageSeoData(BaseModel):
    url: str
    status_code: int = 200
    title: str = ""
    meta_description: str = ""
    meta_robots: str = ""
    canonical_url: str = ""
    h1_tags: List[str] = Field(default_factory=list)
    h2_tags: List[str] = Field(default_factory=list)
    h3_tags: List[str] = Field(default_factory=list)
    content_text: str = ""
    content_length: int = 0
    internal_links: List[str] = Field(default_factory=list)
    external_links: List[str] = Field(default_factory=list)
    images_without_alt: int = 0
    schema_types: List[str] = Field(default_factory=list)


class IntentClassification(BaseModel):
    keyword: str
    primary_intent: str
    confidence: float
    secondary_intents: List[Dict] = Field(default_factory=list)
    signals: List[str] = Field(default_factory=list)
    source: str = "dataforseo"


class CompetitorGap(BaseModel):
    keyword: str
    user_url: str
    content_gap: Dict = Field(default_factory=dict)
    heading_gap: Dict = Field(default_factory=dict)
    meta_gap: Dict = Field(default_factory=dict)
    keyword_usage_gap: Dict = Field(default_factory=dict)
    structural_gap: Dict = Field(default_factory=dict)
    top_competitors: List[Dict] = Field(default_factory=list)


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Effort(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionItem(BaseModel):
    id: str
    category: str  # content, meta, structure, ux, intent
    title: str
    description: str
    keyword: str
    page_url: str
    priority: str
    effort: str
    estimated_impact: str
    specific_suggestions: List[str] = Field(default_factory=list)
