"""
Source configuration for the News Aggregator crawler.
Defines the configuration class for news sources.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SourceConfig:
    """
    Configuration class for a news source.
    """
    name: str
    url: str
    type: str  # rss, html, api
    category: Optional[str] = None
    update_interval: int = 60  # in minutes
    active: bool = True
    id: Optional[int] = None
    
    # Additional settings for specific source types
    rss_settings: Dict[str, Any] = field(default_factory=dict)
    html_settings: Dict[str, Any] = field(default_factory=dict)
    api_settings: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the configuration after initialization."""
        if self.type not in ["rss", "html", "api"]:
            raise ValueError(f"Invalid source type: {self.type}. Must be one of: rss, html, api")
        
        if not self.name or not self.url:
            raise ValueError("Source name and URL are required")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SourceConfig':
        """Create a configuration from a dictionary."""
        return cls(**data)


def load_sources_from_file(file_path: str) -> List[SourceConfig]:
    """
    Load source configurations from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of SourceConfig objects
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"Sources file not found: {file_path}")
            return []
        
        with open(file_path, 'r') as f:
            sources_data = json.load(f)
        
        sources = []
        for source_data in sources_data:
            try:
                source = SourceConfig.from_dict(source_data)
                sources.append(source)
            except Exception as e:
                logger.error(f"Error loading source configuration: {e}")
        
        logger.info(f"Loaded {len(sources)} sources from {file_path}")
        return sources
    except Exception as e:
        logger.error(f"Failed to load sources from file: {e}")
        return []


def save_sources_to_file(sources: List[SourceConfig], file_path: str) -> bool:
    """
    Save source configurations to a JSON file.
    
    Args:
        sources: List of SourceConfig objects
        file_path: Path to the JSON file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        sources_data = [source.to_dict() for source in sources]
        
        with open(file_path, 'w') as f:
            json.dump(sources_data, f, indent=2)
        
        logger.info(f"Saved {len(sources)} sources to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save sources to file: {e}")
        return False


# Default sources configuration
DEFAULT_SOURCES = [
    SourceConfig(
        name="CNN",
        url="http://rss.cnn.com/rss/edition.rss",
        type="rss",
        category="news",
        update_interval=30
    ),
    SourceConfig(
        name="BBC News",
        url="http://feeds.bbci.co.uk/news/rss.xml",
        type="rss",
        category="news",
        update_interval=30
    ),
    SourceConfig(
        name="Reuters",
        url="http://feeds.reuters.com/reuters/topNews",
        type="rss",
        category="news",
        update_interval=30
    ),
    SourceConfig(
        name="TechCrunch",
        url="https://techcrunch.com/feed/",
        type="rss",
        category="technology",
        update_interval=60
    ),
    SourceConfig(
        name="Hacker News",
        url="https://news.ycombinator.com/",
        type="html",
        category="technology",
        update_interval=60,
        html_settings={
            "article_selector": ".athing",
            "title_selector": ".title a",
            "link_selector": ".title a",
            "metadata_selector": ".subtext"
        }
    ),
    SourceConfig(
        name="GitHub Trending",
        url="https://github.com/trending",
        type="html",
        category="technology",
        update_interval=1440,  # once a day
        html_settings={
            "article_selector": "article.Box-row",
            "title_selector": "h1.h3 a",
            "link_selector": "h1.h3 a",
            "description_selector": "p"
        }
    ),
    SourceConfig(
        name="New York Times",
        url="https://api.nytimes.com/svc/topstories/v2/home.json",
        type="api",
        category="news",
        update_interval=60,
        api_settings={
            "api_key_param": "api-key",
            "api_key_env": "NYT_API_KEY",
            "response_format": "json",
            "articles_path": "results",
            "mapping": {
                "title": "title",
                "url": "url",
                "summary": "abstract",
                "published_at": "published_date",
                "author": "byline",
                "image_url": "multimedia.0.url"
            }
        }
    )
]


def get_default_sources() -> List[SourceConfig]:
    """Get the default source configurations."""
    return DEFAULT_SOURCES.copy()


def get_sources(file_path: Optional[str] = None) -> List[SourceConfig]:
    """
    Get source configurations from a file or use defaults.
    
    Args:
        file_path: Path to the sources JSON file
        
    Returns:
        List of SourceConfig objects
    """
    if file_path and os.path.exists(file_path):
        sources = load_sources_from_file(file_path)
        if sources:
            return sources
    
    logger.info("Using default sources configuration")
    return get_default_sources()