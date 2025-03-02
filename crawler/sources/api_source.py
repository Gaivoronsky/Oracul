"""
API source implementation for the News Aggregator crawler.
Handles fetching news from external APIs.
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import aiohttp
from dateutil import parser as date_parser

from crawler.sources.base import BaseSource
from crawler.settings.sources_config import SourceConfig

# Configure logging
logger = logging.getLogger(__name__)


class APISource(BaseSource):
    """
    API source implementation.
    Fetches news articles from external APIs.
    """
    
    def __init__(self, config: SourceConfig):
        """
        Initialize the API source.
        
        Args:
            config: Source configuration
        """
        super().__init__(config)
        
        # Validate source type
        if config.type != "api":
            raise ValueError(f"Invalid source type for APISource: {config.type}")
        
        # Get API-specific settings
        self.api_settings = config.api_settings or {}
        self.method = self.api_settings.get("method", "GET")
        self.headers = self.api_settings.get("headers", {})
        self.params = self.api_settings.get("params", {})
        self.body = self.api_settings.get("body")
        self.auth = self.api_settings.get("auth", {})
        self.timeout = self.api_settings.get("timeout", 30)
        
        # Response parsing settings
        self.response_format = self.api_settings.get("response_format", "json")
        self.articles_path = self.api_settings.get("articles_path", "")
        self.mapping = self.api_settings.get("mapping", {})
        
        # Pagination settings
        self.pagination = self.api_settings.get("pagination", {})
        self.page_param = self.pagination.get("page_param")
        self.page_size_param = self.pagination.get("page_size_param")
        self.page_size = self.pagination.get("page_size", 10)
        self.max_pages = self.pagination.get("max_pages", 1)
        self.total_path = self.pagination.get("total_path")
        self.next_page_path = self.pagination.get("next_page_path")
        
        # Authentication
        self.auth_type = self.auth.get("type")
        self.auth_token = self.auth.get("token")
        self.auth_username = self.auth.get("username")
        self.auth_password = self.auth.get("password")
        
        # Add authentication headers if provided
        if self.auth_type == "bearer" and self.auth_token:
            self.headers["Authorization"] = f"Bearer {self.auth_token}"
        elif self.auth_type == "basic" and self.auth_username and self.auth_password:
            import base64
            auth_string = f"{self.auth_username}:{self.auth_password}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            self.headers["Authorization"] = f"Basic {encoded_auth}"
        elif self.auth_type == "api_key" and self.auth_token:
            key_name = self.auth.get("key_name", "api_key")
            key_location = self.auth.get("key_location", "query")
            
            if key_location == "query":
                self.params[key_name] = self.auth_token
            elif key_location == "header":
                self.headers[key_name] = self.auth_token
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch articles from the API.
        
        Returns:
            List of article data dictionaries
        """
        try:
            articles = []
            current_page = 1
            has_more = True
            
            # Fetch pages until max_pages is reached or no more results
            while has_more and current_page <= self.max_pages:
                page_articles, has_more = await self._fetch_page(current_page)
                articles.extend(page_articles)
                
                if not has_more or not self.page_param:
                    break
                
                current_page += 1
            
            logger.info(f"Fetched {len(articles)} articles from API source {self.name}")
            return articles
        except Exception as e:
            logger.error(f"Error fetching API source {self.name}: {e}")
            return []
    
    async def _fetch_page(self, page: int) -> tuple[List[Dict[str, Any]], bool]:
        """
        Fetch a single page of results from the API.
        
        Args:
            page: Page number
            
        Returns:
            Tuple of (list of article data dictionaries, boolean indicating if more pages exist)
        """
        try:
            # Prepare request parameters
            url = self.url
            headers = self.headers.copy()
            params = self.params.copy()
            data = self.body
            
            # Add pagination parameters if needed
            if self.page_param:
                params[self.page_param] = page
            if self.page_size_param:
                params[self.page_size_param] = self.page_size
            
            # Make the request
            async with aiohttp.ClientSession() as session:
                if self.method.upper() == "GET":
                    async with session.get(url, headers=headers, params=params, timeout=self.timeout) as response:
                        if response.status != 200:
                            logger.error(f"Failed to fetch API {self.name}: HTTP {response.status}")
                            return [], False
                        
                        if self.response_format == "json":
                            response_data = await response.json()
                        else:
                            response_data = await response.text()
                
                elif self.method.upper() == "POST":
                    async with session.post(url, headers=headers, params=params, json=data, timeout=self.timeout) as response:
                        if response.status != 200:
                            logger.error(f"Failed to fetch API {self.name}: HTTP {response.status}")
                            return [], False
                        
                        if self.response_format == "json":
                            response_data = await response.json()
                        else:
                            response_data = await response.text()
                
                else:
                    logger.error(f"Unsupported HTTP method for API {self.name}: {self.method}")
                    return [], False
            
            # Parse response
            if self.response_format == "json":
                articles = self._parse_json_response(response_data)
            else:
                articles = self._parse_text_response(response_data)
            
            # Check if more pages exist
            has_more = self._check_has_more_pages(response_data, page, len(articles))
            
            return articles, has_more
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching API {self.name}")
            return [], False
        except Exception as e:
            logger.error(f"Error fetching page {page} from API {self.name}: {e}")
            return [], False
    
    def _parse_json_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse a JSON API response into articles.
        
        Args:
            response_data: JSON response data
            
        Returns:
            List of article data dictionaries
        """
        try:
            # Extract articles array from response using articles_path
            articles_data = response_data
            if self.articles_path:
                for key in self.articles_path.split('.'):
                    if key.isdigit():
                        key = int(key)
                    if isinstance(articles_data, dict) and key in articles_data:
                        articles_data = articles_data[key]
                    elif isinstance(articles_data, list) and isinstance(key, int) and key < len(articles_data):
                        articles_data = articles_data[key]
                    else:
                        logger.error(f"Invalid articles_path '{self.articles_path}' for API {self.name}")
                        return []
            
            # Ensure articles_data is a list
            if not isinstance(articles_data, list):
                if isinstance(articles_data, dict):
                    articles_data = [articles_data]
                else:
                    logger.error(f"Expected list of articles but got {type(articles_data)} for API {self.name}")
                    return []
            
            # Parse each article
            articles = []
            for item in articles_data:
                try:
                    article = self._map_article_fields(item)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error parsing article from API {self.name}: {e}")
            
            return articles
        except Exception as e:
            logger.error(f"Error parsing JSON response from API {self.name}: {e}")
            return []
    
    def _parse_text_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse a text API response into articles.
        
        Args:
            response_text: Text response data
            
        Returns:
            List of article data dictionaries
        """
        try:
            # Try to parse as JSON first
            try:
                response_data = json.loads(response_text)
                return self._parse_json_response(response_data)
            except json.JSONDecodeError:
                pass
            
            # If not JSON, treat as a single article
            article = {
                "title": self.name,
                "url": self.url,
                "content": response_text,
                "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                "published_at": datetime.now().isoformat(),
                "source": self.name
            }
            
            return [article]
        except Exception as e:
            logger.error(f"Error parsing text response from API {self.name}: {e}")
            return []
    
    def _map_article_fields(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Map API response fields to article fields using the mapping configuration.
        
        Args:
            item: API response item
            
        Returns:
            Article data dictionary or None if invalid
        """
        try:
            # Default mapping if not provided
            mapping = self.mapping or {
                "title": "title",
                "url": "url",
                "content": "content",
                "summary": "summary",
                "published_at": "publishedAt",
                "author": "author",
                "image_url": "imageUrl",
                "categories": "categories"
            }
            
            # Extract fields using mapping
            article = {}
            
            # Title is required
            title = self._extract_field(item, mapping.get("title", "title"))
            if not title:
                return None
            article["title"] = title
            
            # URL is required
            url = self._extract_field(item, mapping.get("url", "url"))
            if not url:
                return None
            article["url"] = url
            
            # Extract other fields
            article["content"] = self._extract_field(item, mapping.get("content", "content"))
            article["summary"] = self._extract_field(item, mapping.get("summary", "summary"))
            
            # Extract and parse date
            published_at = self._extract_field(item, mapping.get("published_at", "publishedAt"))
            if published_at:
                try:
                    if isinstance(published_at, (int, float)):
                        # Assume timestamp
                        dt = datetime.fromtimestamp(published_at)
                    else:
                        # Assume string
                        dt = date_parser.parse(published_at)
                    article["published_at"] = dt.isoformat()
                except:
                    article["published_at"] = None
            else:
                article["published_at"] = None
            
            # Extract other fields
            article["author"] = self._extract_field(item, mapping.get("author", "author"))
            article["image_url"] = self._extract_field(item, mapping.get("image_url", "imageUrl"))
            
            # Extract categories
            categories = self._extract_field(item, mapping.get("categories", "categories"))
            if categories:
                if isinstance(categories, list):
                    article["categories"] = categories
                elif isinstance(categories, str):
                    article["categories"] = [cat.strip() for cat in categories.split(",")]
                else:
                    article["categories"] = [str(categories)]
            else:
                article["categories"] = []
            
            # Add source name
            article["source"] = self.name
            
            # Add language if specified
            if "language" in self.api_settings:
                article["language"] = self.api_settings["language"]
            
            return article
        except Exception as e:
            logger.error(f"Error mapping article fields for API {self.name}: {e}")
            return None
    
    def _extract_field(self, item: Dict[str, Any], field_path: str) -> Any:
        """
        Extract a field from an item using a dot-notation path.
        
        Args:
            item: Item to extract field from
            field_path: Path to the field using dot notation
            
        Returns:
            Field value or None if not found
        """
        if not field_path:
            return None
        
        try:
            value = item
            for key in field_path.split('.'):
                if key.isdigit():
                    key = int(key)
                if isinstance(value, dict) and key in value:
                    value = value[key]
                elif isinstance(value, list) and isinstance(key, int) and key < len(value):
                    value = value[key]
                else:
                    return None
            return value
        except:
            return None
    
    def _check_has_more_pages(self, response_data: Any, current_page: int, items_count: int) -> bool:
        """
        Check if more pages exist based on the response data.
        
        Args:
            response_data: Response data
            current_page: Current page number
            items_count: Number of items in the current page
            
        Returns:
            Boolean indicating if more pages exist
        """
        # If no pagination is configured, assume no more pages
        if not self.page_param:
            return False
        
        # If no items were returned, assume no more pages
        if items_count == 0:
            return False
        
        # If items count is less than page size, assume no more pages
        if items_count < self.page_size:
            return False
        
        # Check total_path if provided
        if self.total_path and isinstance(response_data, dict):
            try:
                total = response_data
                for key in self.total_path.split('.'):
                    if key.isdigit():
                        key = int(key)
                    if isinstance(total, dict) and key in total:
                        total = total[key]
                    elif isinstance(total, list) and isinstance(key, int) and key < len(total):
                        total = total[key]
                    else:
                        return True
                
                # Calculate total pages
                total_pages = (total + self.page_size - 1) // self.page_size
                return current_page < total_pages
            except:
                return True
        
        # Check next_page_path if provided
        if self.next_page_path and isinstance(response_data, dict):
            try:
                next_page = response_data
                for key in self.next_page_path.split('.'):
                    if key.isdigit():
                        key = int(key)
                    if isinstance(next_page, dict) and key in next_page:
                        next_page = next_page[key]
                    elif isinstance(next_page, list) and isinstance(key, int) and key < len(next_page):
                        next_page = next_page[key]
                    else:
                        return False
                
                return bool(next_page)
            except:
                return False
        
        # Default to assuming more pages if we got a full page of results
        return items_count >= self.page_size