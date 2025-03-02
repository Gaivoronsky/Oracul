"""
Scheduler for the News Aggregator crawler.
Manages scheduling and execution of crawling tasks.
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Awaitable
import random
import signal
import sys
from concurrent.futures import ThreadPoolExecutor

from crawler.settings.sources_config import SourceConfig, get_sources
from crawler.sources.base import BaseSource
from crawler.sources.rss_source import RSSSource
from crawler.sources.html_source import HTMLSource
from crawler.sources.api_source import APISource

# Configure logging
logger = logging.getLogger(__name__)


class CrawlerScheduler:
    """
    Scheduler for the News Aggregator crawler.
    Manages scheduling and execution of crawling tasks.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the crawler scheduler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Configure scheduling options
        self.default_interval = self.config.get("default_interval", 3600)  # 1 hour
        self.min_interval = self.config.get("min_interval", 300)  # 5 minutes
        self.jitter = self.config.get("jitter", 0.1)  # 10% jitter
        self.max_concurrent_tasks = self.config.get("max_concurrent_tasks", 5)
        
        # Configure source options
        self.sources_file = self.config.get("sources_file")
        self.use_default_sources = self.config.get("use_default_sources", True)
        
        # State
        self.sources: List[SourceConfig] = []
        self.source_instances: Dict[str, BaseSource] = {}
        self.last_crawl_time: Dict[str, datetime] = {}
        self.next_crawl_time: Dict[str, datetime] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent_tasks)
        
        # Callbacks
        self.on_article_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
        self.on_error_callback: Optional[Callable[[str, Exception], Awaitable[None]]] = None
        
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
        self.stop()
        sys.exit(0)
    
    async def start(self):
        """
        Start the scheduler.
        """
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting crawler scheduler")
        self.running = True
        
        # Load sources
        await self._load_sources()
        
        # Initialize source instances
        self._initialize_sources()
        
        # Start the main scheduling loop
        asyncio.create_task(self._scheduling_loop())
    
    def stop(self):
        """
        Stop the scheduler.
        """
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        logger.info("Stopping crawler scheduler")
        self.running = False
        
        # Cancel all running tasks
        for source_id, task in self.running_tasks.items():
            if not task.done():
                logger.info(f"Cancelling task for source: {source_id}")
                task.cancel()
        
        # Shutdown executor
        self.executor.shutdown(wait=False)
    
    def register_article_callback(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        """
        Register a callback function to be called for each article.
        
        Args:
            callback: Async callback function that takes an article dictionary
        """
        self.on_article_callback = callback
    
    def register_error_callback(self, callback: Callable[[str, Exception], Awaitable[None]]):
        """
        Register a callback function to be called on errors.
        
        Args:
            callback: Async callback function that takes a source ID and an exception
        """
        self.on_error_callback = callback
    
    async def crawl_source(self, source_id: str) -> List[Dict[str, Any]]:
        """
        Crawl a specific source.
        
        Args:
            source_id: ID of the source to crawl
            
        Returns:
            List of article dictionaries
        """
        if source_id not in self.source_instances:
            raise ValueError(f"Unknown source: {source_id}")
        
        source = self.source_instances[source_id]
        
        try:
            logger.info(f"Crawling source: {source_id}")
            articles = await source.process()
            
            # Update last crawl time
            self.last_crawl_time[source_id] = datetime.now()
            
            # Calculate next crawl time
            interval = source.config.interval or self.default_interval
            interval = max(interval, self.min_interval)
            
            # Add jitter to prevent thundering herd
            if self.jitter > 0:
                jitter_factor = 1.0 + random.uniform(-self.jitter, self.jitter)
                interval = int(interval * jitter_factor)
            
            self.next_crawl_time[source_id] = datetime.now() + timedelta(seconds=interval)
            
            logger.info(f"Crawled source {source_id}: {len(articles)} articles, next crawl at {self.next_crawl_time[source_id]}")
            
            return articles
        except Exception as e:
            logger.error(f"Error crawling source {source_id}: {e}")
            
            # Call error callback if registered
            if self.on_error_callback:
                try:
                    await self.on_error_callback(source_id, e)
                except Exception as callback_error:
                    logger.error(f"Error in error callback for source {source_id}: {callback_error}")
            
            # Update next crawl time for retry
            retry_interval = min(source.config.interval or self.default_interval, 600)  # Max 10 minutes for retry
            self.next_crawl_time[source_id] = datetime.now() + timedelta(seconds=retry_interval)
            
            return []
    
    async def _load_sources(self):
        """
        Load sources from configuration.
        """
        try:
            self.sources = await asyncio.to_thread(
                get_sources, self.sources_file, self.use_default_sources
            )
            logger.info(f"Loaded {len(self.sources)} sources")
        except Exception as e:
            logger.error(f"Error loading sources: {e}")
            self.sources = []
    
    def _initialize_sources(self):
        """
        Initialize source instances.
        """
        for source_config in self.sources:
            try:
                # Create source instance based on type
                if source_config.type == "rss":
                    source = RSSSource(source_config)
                elif source_config.type == "html":
                    source = HTMLSource(source_config)
                elif source_config.type == "api":
                    source = APISource(source_config)
                else:
                    logger.warning(f"Unknown source type: {source_config.type}")
                    continue
                
                # Store source instance
                self.source_instances[source_config.id] = source
                
                # Initialize crawl times
                self.last_crawl_time[source_config.id] = datetime.min
                
                # Set initial next crawl time with jitter to distribute load
                initial_delay = random.randint(5, 60)  # 5-60 seconds
                self.next_crawl_time[source_config.id] = datetime.now() + timedelta(seconds=initial_delay)
                
                logger.info(f"Initialized source: {source_config.id} ({source_config.type})")
            except Exception as e:
                logger.error(f"Error initializing source {source_config.id}: {e}")
    
    async def _scheduling_loop(self):
        """
        Main scheduling loop.
        """
        logger.info("Starting scheduling loop")
        
        while self.running:
            try:
                # Find sources that need to be crawled
                now = datetime.now()
                sources_to_crawl = [
                    source_id for source_id, next_time in self.next_crawl_time.items()
                    if next_time <= now and source_id not in self.running_tasks
                ]
                
                # Start crawling tasks
                for source_id in sources_to_crawl:
                    if not self.running:
                        break
                    
                    # Start task
                    task = asyncio.create_task(self._crawl_task(source_id))
                    self.running_tasks[source_id] = task
                
                # Clean up completed tasks
                completed_tasks = [
                    source_id for source_id, task in self.running_tasks.items()
                    if task.done()
                ]
                
                for source_id in completed_tasks:
                    task = self.running_tasks.pop(source_id)
                    try:
                        # Check for exceptions
                        task.result()
                    except asyncio.CancelledError:
                        logger.info(f"Task for source {source_id} was cancelled")
                    except Exception as e:
                        logger.error(f"Task for source {source_id} failed: {e}")
                
                # Sleep for a short time
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in scheduling loop: {e}")
                await asyncio.sleep(5)
    
    async def _crawl_task(self, source_id: str):
        """
        Task for crawling a source.
        
        Args:
            source_id: ID of the source to crawl
        """
        async with self.semaphore:
            try:
                # Crawl the source
                articles = await self.crawl_source(source_id)
                
                # Process articles
                if articles and self.on_article_callback:
                    for article in articles:
                        try:
                            await self.on_article_callback(article)
                        except Exception as e:
                            logger.error(f"Error in article callback for source {source_id}: {e}")
            except Exception as e:
                logger.error(f"Error in crawl task for source {source_id}: {e}")
    
    async def add_source(self, source_config: SourceConfig) -> bool:
        """
        Add a new source to the scheduler.
        
        Args:
            source_config: Source configuration
            
        Returns:
            True if the source was added, False otherwise
        """
        try:
            # Check if source already exists
            if source_config.id in self.source_instances:
                logger.warning(f"Source already exists: {source_config.id}")
                return False
            
            # Create source instance based on type
            if source_config.type == "rss":
                source = RSSSource(source_config)
            elif source_config.type == "html":
                source = HTMLSource(source_config)
            elif source_config.type == "api":
                source = APISource(source_config)
            else:
                logger.warning(f"Unknown source type: {source_config.type}")
                return False
            
            # Store source instance
            self.source_instances[source_config.id] = source
            
            # Initialize crawl times
            self.last_crawl_time[source_config.id] = datetime.min
            self.next_crawl_time[source_config.id] = datetime.now()
            
            # Add to sources list
            self.sources.append(source_config)
            
            # Save sources to file if specified
            if self.sources_file:
                await asyncio.to_thread(
                    lambda: get_sources(self.sources_file, self.use_default_sources, save=True, sources=self.sources)
                )
            
            logger.info(f"Added source: {source_config.id} ({source_config.type})")
            return True
        except Exception as e:
            logger.error(f"Error adding source {source_config.id}: {e}")
            return False
    
    async def remove_source(self, source_id: str) -> bool:
        """
        Remove a source from the scheduler.
        
        Args:
            source_id: ID of the source to remove
            
        Returns:
            True if the source was removed, False otherwise
        """
        try:
            # Check if source exists
            if source_id not in self.source_instances:
                logger.warning(f"Source does not exist: {source_id}")
                return False
            
            # Cancel any running task
            if source_id in self.running_tasks:
                task = self.running_tasks.pop(source_id)
                if not task.done():
                    task.cancel()
            
            # Remove source instance
            del self.source_instances[source_id]
            
            # Remove crawl times
            if source_id in self.last_crawl_time:
                del self.last_crawl_time[source_id]
            if source_id in self.next_crawl_time:
                del self.next_crawl_time[source_id]
            
            # Remove from sources list
            self.sources = [s for s in self.sources if s.id != source_id]
            
            # Save sources to file if specified
            if self.sources_file:
                await asyncio.to_thread(
                    lambda: get_sources(self.sources_file, self.use_default_sources, save=True, sources=self.sources)
                )
            
            logger.info(f"Removed source: {source_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing source {source_id}: {e}")
            return False
    
    async def update_source(self, source_config: SourceConfig) -> bool:
        """
        Update an existing source in the scheduler.
        
        Args:
            source_config: Source configuration
            
        Returns:
            True if the source was updated, False otherwise
        """
        try:
            # Check if source exists
            if source_config.id not in self.source_instances:
                logger.warning(f"Source does not exist: {source_config.id}")
                return False
            
            # Remove old source
            await self.remove_source(source_config.id)
            
            # Add new source
            return await self.add_source(source_config)
        except Exception as e:
            logger.error(f"Error updating source {source_config.id}: {e}")
            return False
    
    def get_source_status(self, source_id: str = None) -> Dict[str, Any]:
        """
        Get the status of sources.
        
        Args:
            source_id: Optional ID of a specific source
            
        Returns:
            Dictionary with source status information
        """
        try:
            if source_id:
                # Get status for a specific source
                if source_id not in self.source_instances:
                    return {"error": f"Source not found: {source_id}"}
                
                return {
                    "id": source_id,
                    "name": self.source_instances[source_id].name,
                    "type": self.source_instances[source_id].config.type,
                    "url": self.source_instances[source_id].url,
                    "last_crawl": self.last_crawl_time[source_id].isoformat() if self.last_crawl_time[source_id] > datetime.min else None,
                    "next_crawl": self.next_crawl_time[source_id].isoformat() if source_id in self.next_crawl_time else None,
                    "running": source_id in self.running_tasks and not self.running_tasks[source_id].done()
                }
            else:
                # Get status for all sources
                return {
                    "sources": [
                        {
                            "id": source_id,
                            "name": source.name,
                            "type": source.config.type,
                            "url": source.url,
                            "last_crawl": self.last_crawl_time[source_id].isoformat() if self.last_crawl_time[source_id] > datetime.min else None,
                            "next_crawl": self.next_crawl_time[source_id].isoformat() if source_id in self.next_crawl_time else None,
                            "running": source_id in self.running_tasks and not self.running_tasks[source_id].done()
                        }
                        for source_id, source in self.source_instances.items()
                    ],
                    "running": self.running,
                    "total_sources": len(self.source_instances),
                    "active_tasks": len([t for t in self.running_tasks.values() if not t.done()]),
                    "max_concurrent_tasks": self.max_concurrent_tasks
                }
        except Exception as e:
            logger.error(f"Error getting source status: {e}")
            return {"error": str(e)}