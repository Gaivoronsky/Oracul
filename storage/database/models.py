"""
Database models for the News Aggregator application.
Defines the structure of the database tables using SQLAlchemy ORM.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Association tables for many-to-many relationships
article_category = Table(
    'article_category',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

article_entity = Table(
    'article_entity',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id'), primary_key=True),
    Column('entity_id', Integer, ForeignKey('entities.id'), primary_key=True)
)

article_tag = Table(
    'article_tag',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)


class Source(Base):
    """
    News source model.
    Represents a source of news articles (website, RSS feed, API, etc.).
    """
    __tablename__ = 'sources'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    type = Column(String(50), nullable=False)  # rss, html, api
    category = Column(String(100))
    update_interval = Column(Integer, default=60)  # in minutes
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    articles = relationship("Article", back_populates="source")

    def __repr__(self):
        return f"<Source(id={self.id}, name='{self.name}', type='{self.type}')>"


class Article(Base):
    """
    News article model.
    Represents a news article collected from a source.
    """
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    title = Column(String(512), nullable=False)
    url = Column(String(2048), nullable=False, unique=True)
    content = Column(Text)
    summary = Column(Text)
    published_at = Column(DateTime)
    author = Column(String(255))
    image_url = Column(String(2048))
    language = Column(String(10))
    sentiment_score = Column(Float)
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source = relationship("Source", back_populates="articles")
    categories = relationship("Category", secondary=article_category, back_populates="articles")
    entities = relationship("Entity", secondary=article_entity, back_populates="articles")
    tags = relationship("Tag", secondary=article_tag, back_populates="articles")

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:30]}...', source_id={self.source_id})>"


class Category(Base):
    """
    Category model.
    Represents a category for classifying news articles.
    """
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    articles = relationship("Article", secondary=article_category, back_populates="categories")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class Entity(Base):
    """
    Entity model.
    Represents a named entity extracted from news articles (person, organization, location, etc.).
    """
    __tablename__ = 'entities'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50))  # person, organization, location, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    articles = relationship("Article", secondary=article_entity, back_populates="entities")

    def __repr__(self):
        return f"<Entity(id={self.id}, name='{self.name}', type='{self.type}')>"


class Tag(Base):
    """
    Tag model.
    Represents a tag for categorizing news articles.
    """
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    articles = relationship("Article", secondary=article_tag, back_populates="tags")

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"


class CrawlLog(Base):
    """
    Crawl log model.
    Represents a log entry for a crawl operation.
    """
    __tablename__ = 'crawl_logs'

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)
    status = Column(String(50), nullable=False)  # success, error
    articles_found = Column(Integer, default=0)
    articles_added = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    source = relationship("Source")

    def __repr__(self):
        return f"<CrawlLog(id={self.id}, source_id={self.source_id}, status='{self.status}')>"


class ProcessLog(Base):
    """
    Process log model.
    Represents a log entry for a data processing operation.
    """
    __tablename__ = 'process_logs'

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    pipeline_stage = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)  # success, error
    error_message = Column(Text)
    processing_time = Column(Float)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    article = relationship("Article")

    def __repr__(self):
        return f"<ProcessLog(id={self.id}, article_id={self.article_id}, pipeline_stage='{self.pipeline_stage}')>"


class UserActivity(Base):
    """
    User activity model.
    Represents user activity for analytics purposes.
    """
    __tablename__ = 'user_activities'

    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), nullable=False)
    activity_type = Column(String(50), nullable=False)  # view, search, click
    article_id = Column(Integer, ForeignKey('articles.id'))
    search_query = Column(String(512))
    referrer = Column(String(2048))
    user_agent = Column(String(512))
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    article = relationship("Article")

    def __repr__(self):
        return f"<UserActivity(id={self.id}, activity_type='{self.activity_type}')>"