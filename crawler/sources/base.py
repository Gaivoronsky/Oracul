"""
Base source class for the News Aggregator crawler.
Defines the interface for all source types (RSS, HTML, API).
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional

from crawler.settings.sources_config import SourceConfig

# Configure logging
logger = logging.getLogger(__name__)


class BaseSource(ABC):
    """
    Abstract base class for all news sources.
    All source types (RSS, HTML, API) must inherit from this class.
    """
    
    def __init__(self, config: SourceConfig):
        """
        Initialize the source with its configuration.
        
        Args:
            config: Source configuration
        """
        self.config = config
        self.name = config.name
        self.url = config.url
        self.type = config.type
        self.category = config.category
        self.update_interval = config.update_interval
        self.active = config.active
        
        # Initialize statistics
        self.stats = {
            "articles_found": 0,
            "articles_processed": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
        
        logger.info(f"Initialized {self.type} source: {self.name}")
    
    @abstractmethod
    async def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch articles from the source.
        
        Returns:
            List of article data dictionaries
        """
        pass
    
    async def process(self) -> Dict[str, Any]:
        """
        Process the source to fetch and normalize articles.
        
        Returns:
            Dictionary with processing statistics
        """
        self.stats["start_time"] = datetime.utcnow()
        
        try:
            # Fetch articles
            articles = await self.fetch()
            self.stats["articles_found"] = len(articles)
            
            # Normalize articles
            normalized_articles = []
            for article in articles:
                try:
                    normalized = self.normalize_article(article)
                    if normalized:
                        normalized_articles.append(normalized)
                        self.stats["articles_processed"] += 1
                except Exception as e:
                    logger.error(f"Error normalizing article from {self.name}: {e}")
                    self.stats["errors"] += 1
            
            logger.info(f"Processed {self.name}: found {self.stats['articles_found']} articles, "
                        f"processed {self.stats['articles_processed']}, errors {self.stats['errors']}")
            
            self.stats["end_time"] = datetime.utcnow()
            return {
                "source": self.name,
                "source_id": self.config.id,
                "articles": normalized_articles,
                "stats": self.stats
            }
        except Exception as e:
            logger.error(f"Error processing source {self.name}: {e}")
            self.stats["errors"] += 1
            self.stats["end_time"] = datetime.utcnow()
            return {
                "source": self.name,
                "source_id": self.config.id,
                "articles": [],
                "stats": self.stats,
                "error": str(e)
            }
    
    def normalize_article(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize article data to a standard format.
        
        Args:
            article: Raw article data
            
        Returns:
            Normalized article data or None if invalid
        """
        # Check required fields
        if not article.get("title") or not article.get("url"):
            logger.warning(f"Article from {self.name} missing required fields")
            return None
        
        # Create normalized article
        normalized = {
            "title": article.get("title"),
            "url": article.get("url"),
            "content": article.get("content"),
            "summary": article.get("summary"),
            "published_at": article.get("published_at"),
            "author": article.get("author"),
            "image_url": article.get("image_url"),
            "source_id": self.config.id,
            "source_name": self.name,
            "language": article.get("language"),
            "categories": article.get("categories", [])
        }
        
        # Add source category if not in categories
        if self.category and self.category not in normalized["categories"]:
            normalized["categories"].append(self.category)
        
        return normalized
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', url='{self.url}')>"