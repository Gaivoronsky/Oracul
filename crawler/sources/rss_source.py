"""
RSS source implementation for the News Aggregator crawler.
Handles fetching and parsing RSS feeds.
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import feedparser
import aiohttp
from dateutil import parser as date_parser

from crawler.sources.base import BaseSource
from crawler.settings.sources_config import SourceConfig

# Configure logging
logger = logging.getLogger(__name__)


class RSSSource(BaseSource):
    """
    RSS feed source implementation.
    Fetches and parses RSS feeds to extract news articles.
    """
    
    def __init__(self, config: SourceConfig):
        """
        Initialize the RSS source.
        
        Args:
            config: Source configuration
        """
        super().__init__(config)
        
        # Validate source type
        if config.type != "rss":
            raise ValueError(f"Invalid source type for RSSSource: {config.type}")
        
        # Get RSS-specific settings
        self.rss_settings = config.rss_settings or {}
        self.user_agent = self.rss_settings.get("user_agent", "NewsAggregator/1.0")
        self.timeout = self.rss_settings.get("timeout", 30)
        self.max_items = self.rss_settings.get("max_items", 100)
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch articles from the RSS feed.
        
        Returns:
            List of article data dictionaries
        """
        try:
            # Fetch RSS feed content
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": self.user_agent}
                async with session.get(self.url, headers=headers, timeout=self.timeout) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch RSS feed {self.name}: HTTP {response.status}")
                        return []
                    
                    content = await response.text()
            
            # Parse RSS feed
            feed = feedparser.parse(content)
            
            if feed.bozo:
                logger.warning(f"RSS feed {self.name} has format issues: {feed.bozo_exception}")
            
            # Extract articles
            articles = []
            for entry in feed.entries[:self.max_items]:
                try:
                    article = self._parse_entry(entry, feed.feed)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error parsing RSS entry from {self.name}: {e}")
            
            logger.info(f"Fetched {len(articles)} articles from RSS feed {self.name}")
            return articles
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching RSS feed {self.name}")
            return []
        except Exception as e:
            logger.error(f"Error fetching RSS feed {self.name}: {e}")
            return []
    
    def _parse_entry(self, entry: Dict[str, Any], feed_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse an RSS entry into an article.
        
        Args:
            entry: RSS entry
            feed_info: RSS feed information
            
        Returns:
            Article data dictionary or None if invalid
        """
        # Check required fields
        if not entry.get("title") or not entry.get("link"):
            return None
        
        # Extract published date
        published_at = None
        for date_field in ["published", "updated", "created", "pubDate"]:
            if date_field in entry:
                try:
                    published_at = date_parser.parse(entry[date_field])
                    break
                except:
                    pass
        
        # Extract content
        content = None
        summary = None
        
        # Try to get content from various fields
        if "content" in entry and entry.content:
            for content_item in entry.content:
                if content_item.get("type") == "text/html":
                    content = content_item.value
                    break
        
        # If no content found, try other fields
        if not content:
            for content_field in ["content", "description", "summary"]:
                if content_field in entry and entry[content_field]:
                    content = entry[content_field]
                    break
        
        # Extract summary
        for summary_field in ["summary", "description", "subtitle"]:
            if summary_field in entry and entry[summary_field]:
                summary = entry[summary_field]
                break
        
        # Extract author
        author = None
        if "author" in entry:
            author = entry.author
        elif "author_detail" in entry and "name" in entry.author_detail:
            author = entry.author_detail.name
        
        # Extract image URL
        image_url = None
        if "media_content" in entry and entry.media_content:
            for media in entry.media_content:
                if media.get("medium") == "image" or media.get("type", "").startswith("image/"):
                    image_url = media.get("url")
                    break
        
        if not image_url and "media_thumbnail" in entry and entry.media_thumbnail:
            image_url = entry.media_thumbnail[0].get("url")
        
        if not image_url and "links" in entry:
            for link in entry.links:
                if link.get("type", "").startswith("image/"):
                    image_url = link.get("href")
                    break
        
        # Extract categories
        categories = []
        if "tags" in entry:
            categories = [tag.term for tag in entry.tags if hasattr(tag, "term")]
        elif "categories" in entry:
            categories = [cat for cat in entry.categories if cat]
        
        # Create article
        article = {
            "title": entry.title,
            "url": entry.link,
            "content": content,
            "summary": summary,
            "published_at": published_at.isoformat() if published_at else None,
            "author": author,
            "image_url": image_url,
            "categories": categories,
            "language": feed_info.get("language")
        }
        
        return article