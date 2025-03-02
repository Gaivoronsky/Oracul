"""
Main entry point for the News Aggregator crawler.
Initializes and runs the crawler scheduler.
"""

import os
import sys
import logging
import asyncio
import argparse
import json
from typing import Dict, Any, List, Optional
import signal

from crawler.scheduler import CrawlerScheduler
from crawler.extractors.text_extractor import TextExtractor
from crawler.extractors.metadata_extractor import MetadataExtractor
from crawler.extractors.media_extractor import MediaExtractor
from crawler.settings.sources_config import SourceConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.getenv('LOG_DIR', 'logs'), 'crawler.log'))
    ]
)
logger = logging.getLogger(__name__)


class CrawlerApp:
    """
    Main application class for the News Aggregator crawler.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the crawler application.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config = self._load_config(config_file)
        
        # Initialize scheduler
        scheduler_config = self.config.get("scheduler", {})
        self.scheduler = CrawlerScheduler(scheduler_config)
        
        # Initialize extractors
        text_extractor_config = self.config.get("text_extractor", {})
        self.text_extractor = TextExtractor(text_extractor_config)
        
        metadata_extractor_config = self.config.get("metadata_extractor", {})
        self.metadata_extractor = MetadataExtractor(metadata_extractor_config)
        
        media_extractor_config = self.config.get("media_extractor", {})
        self.media_extractor = MediaExtractor(media_extractor_config)
        
        # Register callbacks
        self.scheduler.register_article_callback(self.process_article)
        self.scheduler.register_error_callback(self.handle_error)
        
        # Initialize storage client
        self.storage_client = None
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
    
    def _handle_signal(self, sig, frame):
        """
        Handle termination signals.
        
        Args:
            sig: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {sig}, shutting down...")
        asyncio.create_task(self.stop())
    
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_file: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        config = {}
        
        # Default configuration
        default_config = {
            "scheduler": {
                "default_interval": 3600,  # 1 hour
                "min_interval": 300,  # 5 minutes
                "jitter": 0.1,  # 10% jitter
                "max_concurrent_tasks": 5,
                "sources_file": os.getenv("SOURCES_CONFIG_FILE", "sources.json"),
                "use_default_sources": True
            },
            "text_extractor": {
                "extraction_method": "auto",
                "fallback_methods": ["trafilatura", "newspaper", "readability", "basic"],
                "min_content_length": 100,
                "max_content_length": 100000,
                "clean_html": True,
                "normalize_whitespace": True,
                "remove_ads": True
            },
            "metadata_extractor": {
                "extraction_method": "auto",
                "fallback_methods": ["newspaper", "opengraph", "meta", "json_ld", "basic"]
            },
            "media_extractor": {
                "extract_images": True,
                "extract_videos": True,
                "extract_audio": True,
                "max_images": 10,
                "min_image_width": 200,
                "min_image_height": 200,
                "prefer_high_res": True
            },
            "storage": {
                "type": "database",
                "connection_string": os.getenv("DATABASE_URL", "sqlite:///news.db"),
                "batch_size": 10
            }
        }
        
        # Update with environment variables
        env_config = {}
        for key, value in os.environ.items():
            if key.startswith("CRAWLER_"):
                parts = key[8:].lower().split("_")
                current = env_config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
        
        # Update with file configuration
        file_config = {}
        if config_file:
            try:
                with open(config_file, "r") as f:
                    file_config = json.load(f)
            except Exception as e:
                logger.error(f"Error loading configuration file: {e}")
        
        # Merge configurations
        config = self._merge_dicts(default_config, env_config)
        config = self._merge_dicts(config, file_config)
        
        return config
    
    def _merge_dicts(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge two dictionaries.
        
        Args:
            dict1: First dictionary
            dict2: Second dictionary
            
        Returns:
            Merged dictionary
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value
        
        return result
    
    async def start(self):
        """
        Start the crawler application.
        """
        logger.info("Starting crawler application")
        
        # Initialize storage client
        await self._initialize_storage()
        
        # Start scheduler
        await self.scheduler.start()
    
    async def stop(self):
        """
        Stop the crawler application.
        """
        logger.info("Stopping crawler application")
        
        # Stop scheduler
        self.scheduler.stop()
        
        # Close storage client
        await self._close_storage()
    
    async def _initialize_storage(self):
        """
        Initialize the storage client.
        """
        try:
            storage_config = self.config.get("storage", {})
            storage_type = storage_config.get("type", "database")
            
            if storage_type == "database":
                # Import here to avoid circular imports
                from storage.database.repository import ArticleRepository
                
                connection_string = storage_config.get("connection_string", "sqlite:///news.db")
                self.storage_client = ArticleRepository(connection_string)
                logger.info(f"Initialized database storage client with connection string: {connection_string}")
            
            elif storage_type == "elasticsearch":
                # Import here to avoid circular imports
                from storage.search.elasticsearch import ElasticsearchClient
                
                hosts = storage_config.get("hosts", ["localhost:9200"])
                index_name = storage_config.get("index_name", "news")
                self.storage_client = ElasticsearchClient(hosts, index_name)
                logger.info(f"Initialized Elasticsearch storage client with hosts: {hosts}")
            
            else:
                logger.warning(f"Unknown storage type: {storage_type}")
        except Exception as e:
            logger.error(f"Error initializing storage client: {e}")
    
    async def _close_storage(self):
        """
        Close the storage client.
        """
        if self.storage_client:
            try:
                await self.storage_client.close()
                logger.info("Closed storage client")
            except Exception as e:
                logger.error(f"Error closing storage client: {e}")
    
    async def process_article(self, article: Dict[str, Any]):
        """
        Process an article.
        
        Args:
            article: Article data dictionary
        """
        try:
            # Extract HTML content if available
            if "content" in article and "<html" in article["content"].lower():
                article["html_content"] = article["content"]
            
            # Extract text content
            article = await self.text_extractor.extract(article)
            
            # Extract metadata
            article = await self.metadata_extractor.extract(article)
            
            # Extract media
            article = await self.media_extractor.extract(article)
            
            # Store article
            if self.storage_client:
                await self.storage_client.create_article(article)
            
            logger.info(f"Processed article: {article.get('title', 'Untitled')} from {article.get('source', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error processing article: {e}")
    
    async def handle_error(self, source_id: str, error: Exception):
        """
        Handle an error from a source.
        
        Args:
            source_id: ID of the source
            error: Exception that occurred
        """
        logger.error(f"Error from source {source_id}: {error}")
        
        # Log error to storage
        if self.storage_client and hasattr(self.storage_client, "create_crawl_log"):
            try:
                log_entry = {
                    "source_id": source_id,
                    "status": "error",
                    "message": str(error),
                    "timestamp": None  # Will be set by the repository
                }
                await self.storage_client.create_crawl_log(log_entry)
            except Exception as e:
                logger.error(f"Error logging to storage: {e}")


async def main():
    """
    Main entry point.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="News Aggregator Crawler")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--source", help="Crawl a specific source")
    parser.add_argument("--list-sources", action="store_true", help="List available sources")
    parser.add_argument("--add-source", help="Add a new source (JSON format)")
    parser.add_argument("--remove-source", help="Remove a source by ID")
    parser.add_argument("--update-source", help="Update a source (JSON format)")
    args = parser.parse_args()
    
    # Create crawler application
    app = CrawlerApp(args.config)
    
    # Handle commands
    if args.list_sources:
        # Start the app to load sources
        await app.start()
        
        # Get source status
        status = app.scheduler.get_source_status()
        
        # Print sources
        print(json.dumps(status, indent=2))
        
        # Stop the app
        await app.stop()
        return
    
    if args.add_source:
        # Parse source configuration
        try:
            source_config_dict = json.loads(args.add_source)
            source_config = SourceConfig(**source_config_dict)
        except Exception as e:
            logger.error(f"Error parsing source configuration: {e}")
            return
        
        # Start the app to load sources
        await app.start()
        
        # Add source
        result = await app.scheduler.add_source(source_config)
        
        if result:
            print(f"Added source: {source_config.id}")
        else:
            print(f"Failed to add source: {source_config.id}")
        
        # Stop the app
        await app.stop()
        return
    
    if args.remove_source:
        # Start the app to load sources
        await app.start()
        
        # Remove source
        result = await app.scheduler.remove_source(args.remove_source)
        
        if result:
            print(f"Removed source: {args.remove_source}")
        else:
            print(f"Failed to remove source: {args.remove_source}")
        
        # Stop the app
        await app.stop()
        return
    
    if args.update_source:
        # Parse source configuration
        try:
            source_config_dict = json.loads(args.update_source)
            source_config = SourceConfig(**source_config_dict)
        except Exception as e:
            logger.error(f"Error parsing source configuration: {e}")
            return
        
        # Start the app to load sources
        await app.start()
        
        # Update source
        result = await app.scheduler.update_source(source_config)
        
        if result:
            print(f"Updated source: {source_config.id}")
        else:
            print(f"Failed to update source: {source_config.id}")
        
        # Stop the app
        await app.stop()
        return
    
    if args.source:
        # Start the app to load sources
        await app.start()
        
        # Crawl specific source
        try:
            articles = await app.scheduler.crawl_source(args.source)
            print(f"Crawled {len(articles)} articles from source: {args.source}")
        except Exception as e:
            logger.error(f"Error crawling source {args.source}: {e}")
        
        # Stop the app
        await app.stop()
        return
    
    # Start the app normally
    await app.start()
    
    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())