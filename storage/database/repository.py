"""
Database repository for the News Aggregator application.
Provides an interface for performing CRUD operations on database models.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Type, TypeVar, Generic, Union

from sqlalchemy import create_engine, func, desc, asc
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import sessionmaker, Session, Query
from sqlalchemy.sql import text

from dotenv import load_dotenv

from .models import Base, Source, Article, Category, Entity, Tag, CrawlLog, ProcessLog, UserActivity
from .schemas import SourceCreate, ArticleCreate, CategoryCreate, EntityCreate, TagCreate

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for ORM models
T = TypeVar('T')

# Database URL from environment variable or default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./news_aggregator.db")
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))


def get_engine():
    """
    Create and return a SQLAlchemy engine instance.
    """
    if DATABASE_URL.startswith("sqlite"):
        # SQLite doesn't support connection pooling
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
    else:
        # PostgreSQL, MySQL, etc. with connection pooling
        engine = create_engine(
            DATABASE_URL,
            pool_size=DATABASE_POOL_SIZE,
            max_overflow=DATABASE_MAX_OVERFLOW
        )
    return engine


def get_session():
    """
    Create and return a SQLAlchemy session.
    """
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


class BaseRepository(Generic[T]):
    """
    Base repository class with common CRUD operations.
    """
    def __init__(self, model: Type[T]):
        self.model = model
        self.session = get_session()

    def close(self):
        """Close the session."""
        self.session.close()

    def get(self, id: int) -> Optional[T]:
        """Get an object by ID."""
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all objects with pagination."""
        return self.session.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: Dict[str, Any]) -> T:
        """Create a new object."""
        obj = self.model(**obj_in)
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def update(self, id: int, obj_in: Dict[str, Any]) -> Optional[T]:
        """Update an existing object."""
        obj = self.get(id)
        if obj:
            for key, value in obj_in.items():
                if hasattr(obj, key) and value is not None:
                    setattr(obj, key, value)
            self.session.commit()
            self.session.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        """Delete an object by ID."""
        obj = self.get(id)
        if obj:
            self.session.delete(obj)
            self.session.commit()
            return True
        return False

    def count(self) -> int:
        """Count all objects."""
        return self.session.query(func.count(self.model.id)).scalar()


class SourceRepository(BaseRepository[Source]):
    """
    Repository for Source model.
    """
    def __init__(self):
        super().__init__(Source)

    def get_by_name(self, name: str) -> Optional[Source]:
        """Get a source by name."""
        return self.session.query(Source).filter(Source.name == name).first()

    def get_by_url(self, url: str) -> Optional[Source]:
        """Get a source by URL."""
        return self.session.query(Source).filter(Source.url == url).first()

    def get_active_sources(self) -> List[Source]:
        """Get all active sources."""
        return self.session.query(Source).filter(Source.active == True).all()

    def create_source(self, source_in: SourceCreate) -> Source:
        """Create a new source."""
        source_data = source_in.dict()
        return self.create(source_data)


class ArticleRepository(BaseRepository[Article]):
    """
    Repository for Article model.
    """
    def __init__(self):
        super().__init__(Article)

    def get_by_url(self, url: str) -> Optional[Article]:
        """Get an article by URL."""
        return self.session.query(Article).filter(Article.url == url).first()

    def get_by_source(self, source_id: int, skip: int = 0, limit: int = 100) -> List[Article]:
        """Get articles by source ID."""
        return self.session.query(Article).filter(Article.source_id == source_id).offset(skip).limit(limit).all()

    def get_latest(self, skip: int = 0, limit: int = 100) -> List[Article]:
        """Get latest articles."""
        return self.session.query(Article).order_by(desc(Article.published_at)).offset(skip).limit(limit).all()

    def create_article(self, article_in: ArticleCreate) -> Article:
        """Create a new article with related entities."""
        # Extract related entities IDs
        category_ids = article_in.category_ids or []
        entity_ids = article_in.entity_ids or []
        tag_ids = article_in.tag_ids or []
        
        # Create article
        article_data = article_in.dict(exclude={"category_ids", "entity_ids", "tag_ids"})
        article = self.create(article_data)
        
        # Add relationships
        if category_ids:
            categories = self.session.query(Category).filter(Category.id.in_(category_ids)).all()
            article.categories.extend(categories)
            
        if entity_ids:
            entities = self.session.query(Entity).filter(Entity.id.in_(entity_ids)).all()
            article.entities.extend(entities)
            
        if tag_ids:
            tags = self.session.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            article.tags.extend(tags)
            
        self.session.commit()
        self.session.refresh(article)
        return article

    def search(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Article]:
        """
        Search articles by various criteria.
        This is a basic implementation. For production, use a proper search engine like Elasticsearch.
        """
        q = self.session.query(Article)
        
        # Full-text search (basic implementation)
        if query:
            q = q.filter(
                (Article.title.ilike(f"%{query}%")) |
                (Article.content.ilike(f"%{query}%")) |
                (Article.summary.ilike(f"%{query}%"))
            )
        
        # Filter by categories
        if categories:
            q = q.join(Article.categories).filter(Category.name.in_(categories))
        
        # Filter by sources
        if sources:
            q = q.join(Article.source).filter(Source.name.in_(sources))
        
        # Filter by date range
        if date_from:
            q = q.filter(Article.published_at >= date_from)
        if date_to:
            q = q.filter(Article.published_at <= date_to)
        
        # Apply pagination
        return q.offset(skip).limit(limit).all()

    def count_search_results(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> int:
        """Count search results."""
        q = self.session.query(func.count(Article.id))
        
        # Full-text search (basic implementation)
        if query:
            q = q.filter(
                (Article.title.ilike(f"%{query}%")) |
                (Article.content.ilike(f"%{query}%")) |
                (Article.summary.ilike(f"%{query}%"))
            )
        
        # Filter by categories
        if categories:
            q = q.join(Article.categories).filter(Category.name.in_(categories))
        
        # Filter by sources
        if sources:
            q = q.join(Article.source).filter(Source.name.in_(sources))
        
        # Filter by date range
        if date_from:
            q = q.filter(Article.published_at >= date_from)
        if date_to:
            q = q.filter(Article.published_at <= date_to)
        
        return q.scalar()


class CategoryRepository(BaseRepository[Category]):
    """
    Repository for Category model.
    """
    def __init__(self):
        super().__init__(Category)

    def get_by_name(self, name: str) -> Optional[Category]:
        """Get a category by name."""
        return self.session.query(Category).filter(Category.name == name).first()

    def get_or_create(self, name: str, description: Optional[str] = None) -> Category:
        """Get a category by name or create it if it doesn't exist."""
        category = self.get_by_name(name)
        if not category:
            category_data = {"name": name, "description": description}
            category = self.create(category_data)
        return category

    def create_category(self, category_in: CategoryCreate) -> Category:
        """Create a new category."""
        category_data = category_in.dict()
        return self.create(category_data)


class EntityRepository(BaseRepository[Entity]):
    """
    Repository for Entity model.
    """
    def __init__(self):
        super().__init__(Entity)

    def get_by_name_and_type(self, name: str, type: str) -> Optional[Entity]:
        """Get an entity by name and type."""
        return self.session.query(Entity).filter(Entity.name == name, Entity.type == type).first()

    def get_or_create(self, name: str, type: str) -> Entity:
        """Get an entity by name and type or create it if it doesn't exist."""
        entity = self.get_by_name_and_type(name, type)
        if not entity:
            entity_data = {"name": name, "type": type}
            entity = self.create(entity_data)
        return entity

    def create_entity(self, entity_in: EntityCreate) -> Entity:
        """Create a new entity."""
        entity_data = entity_in.dict()
        return self.create(entity_data)

    def get_top_entities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top entities by frequency."""
        result = self.session.query(
            Entity.name,
            Entity.type,
            func.count(Article.id).label("count")
        ).join(
            Entity.articles
        ).group_by(
            Entity.id
        ).order_by(
            desc("count")
        ).limit(limit).all()
        
        return [{"entity": r.name, "type": r.type, "count": r.count} for r in result]


class TagRepository(BaseRepository[Tag]):
    """
    Repository for Tag model.
    """
    def __init__(self):
        super().__init__(Tag)

    def get_by_name(self, name: str) -> Optional[Tag]:
        """Get a tag by name."""
        return self.session.query(Tag).filter(Tag.name == name).first()

    def get_or_create(self, name: str) -> Tag:
        """Get a tag by name or create it if it doesn't exist."""
        tag = self.get_by_name(name)
        if not tag:
            tag_data = {"name": name}
            tag = self.create(tag_data)
        return tag

    def create_tag(self, tag_in: TagCreate) -> Tag:
        """Create a new tag."""
        tag_data = tag_in.dict()
        return self.create(tag_data)


class CrawlLogRepository(BaseRepository[CrawlLog]):
    """
    Repository for CrawlLog model.
    """
    def __init__(self):
        super().__init__(CrawlLog)

    def get_by_source(self, source_id: int, limit: int = 100) -> List[CrawlLog]:
        """Get crawl logs by source ID."""
        return self.session.query(CrawlLog).filter(CrawlLog.source_id == source_id).order_by(desc(CrawlLog.started_at)).limit(limit).all()

    def get_latest(self, limit: int = 100) -> List[CrawlLog]:
        """Get latest crawl logs."""
        return self.session.query(CrawlLog).order_by(desc(CrawlLog.started_at)).limit(limit).all()


class ProcessLogRepository(BaseRepository[ProcessLog]):
    """
    Repository for ProcessLog model.
    """
    def __init__(self):
        super().__init__(ProcessLog)

    def get_by_article(self, article_id: int) -> List[ProcessLog]:
        """Get process logs by article ID."""
        return self.session.query(ProcessLog).filter(ProcessLog.article_id == article_id).order_by(desc(ProcessLog.created_at)).all()

    def get_by_pipeline_stage(self, pipeline_stage: str, limit: int = 100) -> List[ProcessLog]:
        """Get process logs by pipeline stage."""
        return self.session.query(ProcessLog).filter(ProcessLog.pipeline_stage == pipeline_stage).order_by(desc(ProcessLog.created_at)).limit(limit).all()

    def get_latest(self, limit: int = 100) -> List[ProcessLog]:
        """Get latest process logs."""
        return self.session.query(ProcessLog).order_by(desc(ProcessLog.created_at)).limit(limit).all()


class UserActivityRepository(BaseRepository[UserActivity]):
    """
    Repository for UserActivity model.
    """
    def __init__(self):
        super().__init__(UserActivity)

    def get_by_session(self, session_id: str, limit: int = 100) -> List[UserActivity]:
        """Get user activities by session ID."""
        return self.session.query(UserActivity).filter(UserActivity.session_id == session_id).order_by(desc(UserActivity.created_at)).limit(limit).all()

    def get_by_activity_type(self, activity_type: str, limit: int = 100) -> List[UserActivity]:
        """Get user activities by activity type."""
        return self.session.query(UserActivity).filter(UserActivity.activity_type == activity_type).order_by(desc(UserActivity.created_at)).limit(limit).all()

    def get_latest(self, limit: int = 100) -> List[UserActivity]:
        """Get latest user activities."""
        return self.session.query(UserActivity).order_by(desc(UserActivity.created_at)).limit(limit).all()


class AnalyticsRepository:
    """
    Repository for analytics queries.
    """
    def __init__(self):
        self.session = get_session()

    def close(self):
        """Close the session."""
        self.session.close()

    def get_category_distribution(self) -> List[Dict[str, Any]]:
        """Get distribution of articles by category."""
        total_count = self.session.query(func.count(Article.id)).scalar()
        if total_count == 0:
            return []
            
        result = self.session.query(
            Category.name,
            func.count(Article.id).label("count")
        ).join(
            Category.articles
        ).group_by(
            Category.name
        ).order_by(
            desc("count")
        ).all()
        
        return [
            {
                "category": r.name,
                "count": r.count,
                "percentage": round((r.count / total_count) * 100, 2)
            }
            for r in result
        ]

    def get_source_performance(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get performance metrics for news sources."""
        result = self.session.query(
            Source.name,
            func.count(Article.id).label("articles_count"),
            func.avg(Article.sentiment_score).label("average_sentiment")
        ).join(
            Source.articles
        ).group_by(
            Source.id
        ).order_by(
            desc("articles_count")
        ).limit(limit).all()
        
        # Get categories for each source
        source_categories = {}
        for source in result:
            categories = self.session.query(
                Category.name
            ).join(
                Category.articles
            ).join(
                Article.source
            ).filter(
                Source.name == source.name
            ).group_by(
                Category.name
            ).all()
            source_categories[source.name] = [c.name for c in categories]
        
        return [
            {
                "source": r.name,
                "articles_count": r.articles_count,
                "average_sentiment": round(r.average_sentiment or 0.5, 2),
                "categories": source_categories.get(r.name, []),
                "reliability_score": round(min(0.9, (r.articles_count / 100) + 0.5), 2)  # Mock score
            }
            for r in result
        ]

    def get_time_series_data(self, days: int = 7, interval: str = "day") -> List[Dict[str, Any]]:
        """Get time series data for articles."""
        if interval == "hour":
            # Group by hour
            date_trunc = func.date_trunc('hour', Article.published_at)
        elif interval == "day":
            # Group by day
            date_trunc = func.date_trunc('day', Article.published_at)
        elif interval == "month":
            # Group by month
            date_trunc = func.date_trunc('month', Article.published_at)
        else:
            # Default to day
            date_trunc = func.date_trunc('day', Article.published_at)
        
        # Get time series data
        result = self.session.query(
            date_trunc.label("timestamp"),
            func.count(Article.id).label("articles_count"),
            func.count(func.distinct(Article.source_id)).label("sources_count"),
            func.avg(Article.sentiment_score).label("average_sentiment")
        ).filter(
            Article.published_at >= func.now() - func.make_interval(days=days)
        ).group_by(
            "timestamp"
        ).order_by(
            "timestamp"
        ).all()
        
        return [
            {
                "timestamp": r.timestamp.isoformat(),
                "articles_count": r.articles_count,
                "sources_count": r.sources_count,
                "average_sentiment": round(r.average_sentiment or 0.5, 2)
            }
            for r in result
        ]