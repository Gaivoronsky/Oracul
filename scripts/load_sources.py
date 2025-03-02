#!/usr/bin/env python3
"""
News sources loading script.
Loads initial news sources into the database.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'load_sources.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    from storage.database.repository import SourceRepository
    from crawler.settings.sources_config import SourceConfig
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)


# Default sources to load if no sources file is provided
DEFAULT_SOURCES = [
    {
        "name": "CNN",
        "url": "http://rss.cnn.com/rss/edition.rss",
        "type": "rss",
        "category": "news",
        "update_interval": 30,
        "active": True
    },
    {
        "name": "BBC News",
        "url": "http://feeds.bbci.co.uk/news/rss.xml",
        "type": "rss",
        "category": "news",
        "update_interval": 30,
        "active": True
    },
    {
        "name": "Reuters",
        "url": "http://feeds.reuters.com/reuters/topNews",
        "type": "rss",
        "category": "news",
        "update_interval": 30,
        "active": True
    },
    {
        "name": "The Guardian",
        "url": "https://www.theguardian.com/international/rss",
        "type": "rss",
        "category": "news",
        "update_interval": 30,
        "active": True
    },
    {
        "name": "New York Times",
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "type": "rss",
        "category": "news",
        "update_interval": 30,
        "active": True
    },
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "type": "rss",
        "category": "technology",
        "update_interval": 60,
        "active": True
    },
    {
        "name": "Wired",
        "url": "https://www.wired.com/feed/rss",
        "type": "rss",
        "category": "technology",
        "update_interval": 60,
        "active": True
    },
    {
        "name": "ESPN",
        "url": "https://www.espn.com/espn/rss/news",
        "type": "rss",
        "category": "sports",
        "update_interval": 60,
        "active": True
    },
    {
        "name": "National Geographic",
        "url": "https://www.nationalgeographic.com/rss/index.html",
        "type": "rss",
        "category": "science",
        "update_interval": 120,
        "active": True
    },
    {
        "name": "The Economist",
        "url": "https://www.economist.com/rss",
        "type": "rss",
        "category": "business",
        "update_interval": 120,
        "active": True
    }
]


def load_sources_from_file(file_path):
    """Load sources from a JSON file."""
    try:
        logger.info(f"Loading sources from file: {file_path}")
        with open(file_path, 'r') as f:
            sources = json.load(f)
        logger.info(f"Loaded {len(sources)} sources from file")
        return sources
    except Exception as e:
        logger.error(f"Failed to load sources from file: {e}")
        logger.info("Using default sources instead")
        return DEFAULT_SOURCES


def save_sources_to_database(sources):
    """Save sources to the database."""
    try:
        logger.info("Saving sources to database...")
        repo = SourceRepository()
        
        for source_data in sources:
            # Create source config
            config = SourceConfig(
                name=source_data["name"],
                url=source_data["url"],
                type=source_data["type"],
                category=source_data.get("category", "general"),
                update_interval=source_data.get("update_interval", 60),
                active=source_data.get("active", True)
            )
            
            # Save to database
            repo.create_source(config)
            
        logger.info(f"Successfully saved {len(sources)} sources to database")
    except Exception as e:
        logger.error(f"Failed to save sources to database: {e}")
        raise


def main():
    """Main function to load sources."""
    logger.info("Starting sources loading")
    
    try:
        # Check if sources file is provided as argument
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            sources = load_sources_from_file(sys.argv[1])
        else:
            # Look for sources.json in the current directory
            if os.path.exists('sources.json'):
                sources = load_sources_from_file('sources.json')
            else:
                logger.info("No sources file provided, using default sources")
                sources = DEFAULT_SOURCES
        
        # Save sources to database
        save_sources_to_database(sources)
        
        logger.info("Sources loading completed successfully")
    except Exception as e:
        logger.error(f"Sources loading failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()