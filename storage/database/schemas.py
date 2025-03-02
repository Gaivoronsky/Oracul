"""
Pydantic schemas for the News Aggregator application.
Defines schemas for data validation and serialization/deserialization.
"""

from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, HttpUrl, Field, validator


# Base schemas (used for creating objects)
class SourceBase(BaseModel):
    """Base schema for news source."""
    name: str
    url: str
    type: str
    category: Optional[str] = None
    update_interval: int = 60
    active: bool = True


class ArticleBase(BaseModel):
    """Base schema for news article."""
    title: str
    url: str
    content: Optional[str] = None
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    language: Optional[str] = None
    sentiment_score: Optional[float] = None
    source_id: int


class CategoryBase(BaseModel):
    """Base schema for category."""
    name: str
    description: Optional[str] = None


class EntityBase(BaseModel):
    """Base schema for entity."""
    name: str
    type: Optional[str] = None


class TagBase(BaseModel):
    """Base schema for tag."""
    name: str


# Create schemas (used for creating new objects)
class SourceCreate(SourceBase):
    """Schema for creating a new source."""
    pass


class ArticleCreate(ArticleBase):
    """Schema for creating a new article."""
    category_ids: Optional[List[int]] = []
    entity_ids: Optional[List[int]] = []
    tag_ids: Optional[List[int]] = []


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass


class EntityCreate(EntityBase):
    """Schema for creating a new entity."""
    pass


class TagCreate(TagBase):
    """Schema for creating a new tag."""
    pass


# Read schemas (used for returning objects)
class Category(CategoryBase):
    """Schema for returning a category."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class Tag(TagBase):
    """Schema for returning a tag."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class Entity(EntityBase):
    """Schema for returning an entity."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class Source(SourceBase):
    """Schema for returning a source."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ArticleList(BaseModel):
    """Schema for returning a list of articles."""
    id: int
    title: str
    url: str
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    source_id: int
    source_name: str
    image_url: Optional[str] = None
    language: Optional[str] = None
    sentiment_score: Optional[float] = None
    categories: List[str] = []

    class Config:
        orm_mode = True


class Article(ArticleBase):
    """Schema for returning a full article."""
    id: int
    created_at: datetime
    updated_at: datetime
    source: Source
    categories: List[Category] = []
    entities: List[Entity] = []
    tags: List[Tag] = []

    class Config:
        orm_mode = True


# Update schemas (used for updating objects)
class SourceUpdate(BaseModel):
    """Schema for updating a source."""
    name: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    update_interval: Optional[int] = None
    active: Optional[bool] = None


class ArticleUpdate(BaseModel):
    """Schema for updating an article."""
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    language: Optional[str] = None
    sentiment_score: Optional[float] = None
    category_ids: Optional[List[int]] = None
    entity_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None


# Search schemas
class SearchQuery(BaseModel):
    """Schema for search query."""
    q: str
    categories: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    entities: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    language: Optional[str] = None
    sort_by: str = "relevance"
    page: int = 1
    limit: int = 20


class SearchResult(BaseModel):
    """Schema for search results."""
    items: List[ArticleList]
    total: int
    page: int
    limit: int
    pages: int
    query: str


# Analytics schemas
class CategoryDistribution(BaseModel):
    """Schema for category distribution."""
    category: str
    count: int
    percentage: float


class SourcePerformance(BaseModel):
    """Schema for source performance."""
    source: str
    articles_count: int
    average_sentiment: float
    categories: List[str]
    reliability_score: float


class TopEntity(BaseModel):
    """Schema for top entity."""
    entity: str
    type: str
    count: int
    sentiment: float


class TimeSeriesPoint(BaseModel):
    """Schema for time series data point."""
    timestamp: datetime
    articles_count: int
    sources_count: int
    average_sentiment: float


class Stats(BaseModel):
    """Schema for statistics."""
    period: str
    start_time: datetime
    end_time: datetime
    interval: str
    metrics: dict
    time_series: List[TimeSeriesPoint]


# Log schemas
class CrawlLogCreate(BaseModel):
    """Schema for creating a crawl log."""
    source_id: int
    status: str
    articles_found: int = 0
    articles_added: int = 0
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class CrawlLog(CrawlLogCreate):
    """Schema for returning a crawl log."""
    id: int
    source_name: str

    class Config:
        orm_mode = True


class ProcessLogCreate(BaseModel):
    """Schema for creating a process log."""
    article_id: int
    pipeline_stage: str
    status: str
    error_message: Optional[str] = None
    processing_time: float


class ProcessLog(ProcessLogCreate):
    """Schema for returning a process log."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# User activity schemas
class UserActivityCreate(BaseModel):
    """Schema for creating a user activity."""
    session_id: str
    activity_type: str
    article_id: Optional[int] = None
    search_query: Optional[str] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class UserActivity(UserActivityCreate):
    """Schema for returning a user activity."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True