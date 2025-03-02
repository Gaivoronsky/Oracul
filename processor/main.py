"""
Main entry point for the News Aggregator processor.
Initializes and runs the data processing pipeline.
"""

import os
import sys
import logging
import asyncio
import argparse
import json
from typing import Dict, Any, List, Optional
import signal
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.getenv('LOG_DIR', 'logs'), 'processor.log'))
    ]
)
logger = logging.getLogger(__name__)


class ProcessorApp:
    """
    Main application class for the News Aggregator processor.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the processor application.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config = self._load_config(config_file)
        
        # Initialize components
        self.pipeline_config = self.config.get("pipeline", {})
        self.deduplication_config = self.config.get("deduplication", {})
        self.batch_size = self.config.get("batch_size", 100)
        self.processing_interval = self.config.get("processing_interval", 300)  # 5 minutes
        self.running = False
        
        # Initialize pipeline components
        self.pipeline_components = []
        self._initialize_pipeline()
        
        # Initialize deduplication detector
        self.duplicate_detector = None
        self._initialize_deduplication()
        
        # Initialize storage clients
        self.db_client = None
        self.search_client = None
        
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
            "pipeline": {
                "components": ["cleaner", "language_detector", "entity_extractor", "classifier", "sentiment_analyzer"],
                "cleaner": {
                    "remove_html": True,
                    "remove_urls": True,
                    "remove_emails": True,
                    "normalize_whitespace": True,
                    "min_content_length": 100
                },
                "language_detector": {
                    "default_language": "en",
                    "min_confidence": 0.5
                },
                "entity_extractor": {
                    "enabled": True,
                    "models": {
                        "en": "en_core_web_sm",
                        "es": "es_core_news_sm",
                        "fr": "fr_core_news_sm",
                        "de": "de_core_news_sm"
                    },
                    "entity_types": ["PERSON", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "WORK_OF_ART"]
                },
                "classifier": {
                    "enabled": True,
                    "model_path": "models/classifier",
                    "categories": ["politics", "business", "technology", "science", "health", "sports", "entertainment"]
                },
                "sentiment_analyzer": {
                    "enabled": True,
                    "model_path": "models/sentiment",
                    "default_language": "en"
                }
            },
            "deduplication": {
                "enabled": True,
                "similarity_threshold": 0.8,
                "title_weight": 0.6,
                "content_weight": 0.4,
                "max_days_back": 7
            },
            "batch_size": 100,
            "processing_interval": 300,  # 5 minutes
            "database": {
                "connection_string": os.getenv("DATABASE_URL", "sqlite:///news.db")
            },
            "elasticsearch": {
                "hosts": os.getenv("ELASTICSEARCH_HOSTS", "localhost:9200").split(","),
                "index_name": os.getenv("ELASTICSEARCH_INDEX", "news")
            }
        }
        
        # Update with environment variables
        env_config = {}
        for key, value in os.environ.items():
            if key.startswith("PROCESSOR_"):
                parts = key[10:].lower().split("_")
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
    
    def _initialize_pipeline(self):
        """
        Initialize the processing pipeline components.
        """
        try:
            # Get enabled components
            components = self.pipeline_config.get("components", [])
            
            for component_name in components:
                try:
                    component_config = self.pipeline_config.get(component_name, {})
                    
                    if component_name == "cleaner":
                        from processor.pipeline.cleaner import Cleaner
                        component = Cleaner(component_config)
                    
                    elif component_name == "language_detector":
                        from processor.pipeline.language_detector import LanguageDetector
                        component = LanguageDetector(component_config)
                    
                    elif component_name == "entity_extractor":
                        from processor.pipeline.entity_extractor import EntityExtractor
                        component = EntityExtractor(component_config)
                    
                    elif component_name == "classifier":
                        from processor.pipeline.classifier import Classifier
                        component = Classifier(component_config)
                    
                    elif component_name == "sentiment_analyzer":
                        from processor.pipeline.sentiment_analyzer import SentimentAnalyzer
                        component = SentimentAnalyzer(component_config)
                    
                    else:
                        logger.warning(f"Unknown pipeline component: {component_name}")
                        continue
                    
                    self.pipeline_components.append(component)
                    logger.info(f"Initialized pipeline component: {component_name}")
                
                except Exception as e:
                    logger.error(f"Error initializing pipeline component {component_name}: {e}")
        
        except Exception as e:
            logger.error(f"Error initializing pipeline: {e}")
    
    def _initialize_deduplication(self):
        """
        Initialize the deduplication detector.
        """
        try:
            if self.deduplication_config.get("enabled", True):
                from processor.deduplication.duplicate_detector import DuplicateDetector
                self.duplicate_detector = DuplicateDetector(self.deduplication_config)
                logger.info("Initialized duplicate detector")
        except Exception as e:
            logger.error(f"Error initializing duplicate detector: {e}")
    
    async def start(self):
        """
        Start the processor application.
        """
        logger.info("Starting processor application")
        
        # Initialize storage clients
        await self._initialize_storage()
        
        # Start processing loop
        self.running = True
        asyncio.create_task(self._processing_loop())
    
    async def stop(self):
        """
        Stop the processor application.
        """
        logger.info("Stopping processor application")
        
        # Stop processing loop
        self.running = False
        
        # Close storage clients
        await self._close_storage()
    
    async def _initialize_storage(self):
        """
        Initialize the storage clients.
        """
        try:
            # Initialize database client
            from storage.database.repository import ArticleRepository
            
            # Note: ArticleRepository doesn't take a connection string parameter
            # The connection is configured via environment variables
            self.db_client = ArticleRepository()
            logger.info("Initialized database client")
            
            # Initialize search client
            from storage.search.elasticsearch import ElasticsearchClient
            
            es_config = self.config.get("elasticsearch", {})
            hosts = es_config.get("hosts", ["localhost:9200"])
            index_name = es_config.get("index_name", "news")
            self.search_client = ElasticsearchClient(hosts, index_name)
            logger.info(f"Initialized Elasticsearch client with hosts: {hosts}")
        
        except Exception as e:
            logger.error(f"Error initializing storage clients: {e}")
    
    async def _close_storage(self):
        """
        Close the storage clients.
        """
        try:
            if self.db_client:
                await self.db_client.close()
                logger.info("Closed database client")
            
            if self.search_client:
                await self.search_client.close()
                logger.info("Closed Elasticsearch client")
        
        except Exception as e:
            logger.error(f"Error closing storage clients: {e}")
    
    async def _processing_loop(self):
        """
        Main processing loop.
        """
        logger.info("Starting processing loop")
        
        while self.running:
            try:
                # Get unprocessed articles
                articles = await self._get_unprocessed_articles()
                
                if articles:
                    logger.info(f"Processing {len(articles)} articles")
                    
                    # Process articles
                    processed_count = 0
                    for article in articles:
                        try:
                            # Check for duplicates
                            if self.duplicate_detector:
                                is_duplicate, duplicate_id = await self.duplicate_detector.check_duplicate(article, self.db_client)
                                
                                if is_duplicate:
                                    logger.info(f"Article '{article.get('title')}' is a duplicate of {duplicate_id}")
                                    
                                    # Mark as duplicate
                                    article["is_duplicate"] = True
                                    article["duplicate_of"] = duplicate_id
                                    
                                    # Update article
                                    await self.db_client.update_article(article["id"], article)
                                    
                                    # Log processing
                                    await self._log_processing(article["id"], "duplicate", f"Duplicate of {duplicate_id}")
                                    
                                    continue
                            
                            # Run through pipeline
                            processed_article = await self._process_article(article)
                            
                            # Update article in database
                            await self.db_client.update_article(processed_article["id"], processed_article)
                            
                            # Index article in search
                            await self.search_client.index_article(processed_article)
                            
                            # Log processing
                            await self._log_processing(processed_article["id"], "processed", "Successfully processed")
                            
                            processed_count += 1
                        
                        except Exception as e:
                            logger.error(f"Error processing article {article.get('id')}: {e}")
                            
                            # Log error
                            await self._log_processing(article["id"], "error", str(e))
                    
                    logger.info(f"Processed {processed_count} articles")
                
                # Sleep until next processing interval
                await asyncio.sleep(self.processing_interval)
            
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(60)  # Sleep for 1 minute on error
    
    async def _get_unprocessed_articles(self) -> List[Dict[str, Any]]:
        """
        Get unprocessed articles from the database.
        
        Returns:
            List of article dictionaries
        """
        try:
            if not self.db_client:
                return []
            
            # Get articles that haven't been processed yet
            articles = await self.db_client.get_articles(
                processed=False,
                limit=self.batch_size
            )
            
            return articles
        
        except Exception as e:
            logger.error(f"Error getting unprocessed articles: {e}")
            return []
    
    async def _process_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an article through the pipeline.
        
        Args:
            article: Article data dictionary
            
        Returns:
            Processed article data dictionary
        """
        processed_article = article.copy()
        
        # Run through each pipeline component
        for component in self.pipeline_components:
            try:
                processed_article = await component.process(processed_article)
            except Exception as e:
                logger.error(f"Error in pipeline component {component.__class__.__name__}: {e}")
        
        # Mark as processed
        processed_article["processed"] = True
        processed_article["processed_at"] = datetime.now().isoformat()
        
        return processed_article
    
    async def _log_processing(self, article_id: str, status: str, message: str):
        """
        Log processing status.
        
        Args:
            article_id: Article ID
            status: Processing status
            message: Processing message
        """
        try:
            if self.db_client and hasattr(self.db_client, "create_process_log"):
                log_entry = {
                    "article_id": article_id,
                    "status": status,
                    "message": message,
                    "timestamp": None  # Will be set by the repository
                }
                await self.db_client.create_process_log(log_entry)
        except Exception as e:
            logger.error(f"Error logging processing: {e}")
    
    async def process_article(self, article_id: str) -> Dict[str, Any]:
        """
        Process a specific article.
        
        Args:
            article_id: Article ID
            
        Returns:
            Processed article data dictionary
        """
        try:
            # Get article from database
            article = await self.db_client.get_article_by_id(article_id)
            
            if not article:
                raise ValueError(f"Article not found: {article_id}")
            
            # Check for duplicates
            if self.duplicate_detector:
                is_duplicate, duplicate_id = await self.duplicate_detector.check_duplicate(article, self.db_client)
                
                if is_duplicate:
                    logger.info(f"Article '{article.get('title')}' is a duplicate of {duplicate_id}")
                    
                    # Mark as duplicate
                    article["is_duplicate"] = True
                    article["duplicate_of"] = duplicate_id
                    
                    # Update article
                    await self.db_client.update_article(article["id"], article)
                    
                    # Log processing
                    await self._log_processing(article["id"], "duplicate", f"Duplicate of {duplicate_id}")
                    
                    return article
            
            # Process article
            processed_article = await self._process_article(article)
            
            # Update article in database
            await self.db_client.update_article(processed_article["id"], processed_article)
            
            # Index article in search
            await self.search_client.index_article(processed_article)
            
            # Log processing
            await self._log_processing(processed_article["id"], "processed", "Successfully processed")
            
            return processed_article
        
        except Exception as e:
            logger.error(f"Error processing article {article_id}: {e}")
            
            # Log error
            await self._log_processing(article_id, "error", str(e))
            
            raise


async def main():
    """
    Main entry point.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="News Aggregator Processor")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--process", help="Process a specific article by ID")
    parser.add_argument("--reprocess-all", action="store_true", help="Reprocess all articles")
    args = parser.parse_args()
    
    # Create processor application
    app = ProcessorApp(args.config)
    
    # Handle commands
    if args.process:
        # Start the app to initialize components
        await app.start()
        
        try:
            # Process specific article
            processed_article = await app.process_article(args.process)
            print(f"Processed article: {processed_article.get('title')}")
        except Exception as e:
            print(f"Error processing article: {e}")
        
        # Stop the app
        await app.stop()
        return
    
    if args.reprocess_all:
        # Start the app to initialize components
        await app.start()
        
        try:
            # Get all articles
            articles = await app.db_client.get_articles(limit=0)  # No limit
            
            print(f"Reprocessing {len(articles)} articles")
            
            # Process each article
            for article in articles:
                try:
                    # Reset processing flags
                    article["processed"] = False
                    article["processed_at"] = None
                    article["is_duplicate"] = False
                    article["duplicate_of"] = None
                    
                    # Update article
                    await app.db_client.update_article(article["id"], article)
                except Exception as e:
                    print(f"Error resetting article {article.get('id')}: {e}")
            
            print("All articles have been reset for reprocessing")
        except Exception as e:
            print(f"Error reprocessing articles: {e}")
        
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