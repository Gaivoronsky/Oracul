"""
HTML source implementation for the News Aggregator crawler.
Handles fetching and parsing HTML pages.
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import re
import aiohttp
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from crawler.sources.base import BaseSource
from crawler.settings.sources_config import SourceConfig

# Configure logging
logger = logging.getLogger(__name__)


class HTMLSource(BaseSource):
    """
    HTML source implementation.
    Fetches and parses HTML pages to extract news articles.
    """
    
    def __init__(self, config: SourceConfig):
        """
        Initialize the HTML source.
        
        Args:
            config: Source configuration
        """
        super().__init__(config)
        
        # Validate source type
        if config.type != "html":
            raise ValueError(f"Invalid source type for HTMLSource: {config.type}")
        
        # Get HTML-specific settings
        self.html_settings = config.html_settings or {}
        self.user_agent = self.html_settings.get("user_agent", "NewsAggregator/1.0")
        self.timeout = self.html_settings.get("timeout", 30)
        
        # Selectors for extracting content
        self.selectors = self.html_settings.get("selectors", {})
        self.article_selector = self.selectors.get("article", "article, .post, .entry, .news-item")
        self.title_selector = self.selectors.get("title", "h1, h2, .title, .headline")
        self.link_selector = self.selectors.get("link", "a")
        self.content_selector = self.selectors.get("content", ".content, .entry-content, .post-content")
        self.summary_selector = self.selectors.get("summary", ".summary, .excerpt, .description")
        self.date_selector = self.selectors.get("date", ".date, .time, .published, .timestamp")
        self.author_selector = self.selectors.get("author", ".author, .byline")
        self.image_selector = self.selectors.get("image", "img")
        self.category_selector = self.selectors.get("category", ".category, .tag, .topic")
        
        # Date parsing
        self.date_format = self.html_settings.get("date_format")
        self.date_regex = self.html_settings.get("date_regex")
        
        # Pagination
        self.pagination = self.html_settings.get("pagination", {})
        self.next_page_selector = self.pagination.get("next_page", "a.next, .pagination a[rel=next]")
        self.max_pages = self.pagination.get("max_pages", 1)
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch articles from the HTML page.
        
        Returns:
            List of article data dictionaries
        """
        try:
            articles = []
            current_url = self.url
            pages_fetched = 0
            
            # Fetch pages until max_pages is reached or no next page is found
            while current_url and pages_fetched < self.max_pages:
                page_articles = await self._fetch_page(current_url)
                articles.extend(page_articles)
                
                # Get next page URL if pagination is enabled
                if self.max_pages > 1:
                    current_url = await self._get_next_page_url(current_url)
                else:
                    current_url = None
                
                pages_fetched += 1
            
            logger.info(f"Fetched {len(articles)} articles from HTML source {self.name} ({pages_fetched} pages)")
            return articles
        except Exception as e:
            logger.error(f"Error fetching HTML source {self.name}: {e}")
            return []
    
    async def _fetch_page(self, url: str) -> List[Dict[str, Any]]:
        """
        Fetch and parse a single HTML page.
        
        Args:
            url: URL of the page to fetch
            
        Returns:
            List of article data dictionaries
        """
        try:
            # Fetch HTML content
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": self.user_agent}
                async with session.get(url, headers=headers, timeout=self.timeout) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch HTML page {url}: HTTP {response.status}")
                        return []
                    
                    content = await response.text()
            
            # Parse HTML
            soup = BeautifulSoup(content, "html.parser")
            
            # Extract articles
            articles = []
            
            # If article selector is provided, find all article elements
            if self.article_selector:
                article_elements = soup.select(self.article_selector)
                
                for article_element in article_elements:
                    try:
                        article = self._parse_article_element(article_element, url)
                        if article:
                            articles.append(article)
                    except Exception as e:
                        logger.error(f"Error parsing article element from {url}: {e}")
            else:
                # If no article selector, treat the whole page as one article
                try:
                    article = self._parse_page_as_article(soup, url)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error parsing page as article {url}: {e}")
            
            return articles
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching HTML page {url}")
            return []
        except Exception as e:
            logger.error(f"Error fetching HTML page {url}: {e}")
            return []
    
    def _parse_article_element(self, element: BeautifulSoup, base_url: str) -> Optional[Dict[str, Any]]:
        """
        Parse an article element into an article.
        
        Args:
            element: BeautifulSoup element representing an article
            base_url: Base URL for resolving relative links
            
        Returns:
            Article data dictionary or None if invalid
        """
        # Extract title
        title_element = element.select_one(self.title_selector)
        if not title_element:
            return None
        
        title = title_element.get_text().strip()
        if not title:
            return None
        
        # Extract link
        link = None
        link_element = title_element.find("a") if title_element else None
        if not link_element and self.link_selector:
            link_element = element.select_one(self.link_selector)
        
        if link_element and link_element.has_attr("href"):
            link = link_element["href"]
            # Resolve relative URLs
            if link and not (link.startswith("http://") or link.startswith("https://")):
                link = self._resolve_url(base_url, link)
        
        if not link:
            return None
        
        # Extract content
        content = None
        content_element = element.select_one(self.content_selector)
        if content_element:
            content = content_element.get_text().strip()
        
        # Extract summary
        summary = None
        summary_element = element.select_one(self.summary_selector)
        if summary_element:
            summary = summary_element.get_text().strip()
        
        # Extract published date
        published_at = None
        date_element = element.select_one(self.date_selector)
        if date_element:
            date_text = date_element.get_text().strip()
            published_at = self._parse_date(date_text)
        
        # Extract author
        author = None
        author_element = element.select_one(self.author_selector)
        if author_element:
            author = author_element.get_text().strip()
        
        # Extract image URL
        image_url = None
        image_element = element.select_one(self.image_selector)
        if image_element and image_element.has_attr("src"):
            image_url = image_element["src"]
            # Resolve relative URLs
            if image_url and not (image_url.startswith("http://") or image_url.startswith("https://")):
                image_url = self._resolve_url(base_url, image_url)
        
        # Extract categories
        categories = []
        category_elements = element.select(self.category_selector)
        for category_element in category_elements:
            category = category_element.get_text().strip()
            if category:
                categories.append(category)
        
        # Create article
        article = {
            "title": title,
            "url": link,
            "content": content,
            "summary": summary,
            "published_at": published_at.isoformat() if published_at else None,
            "author": author,
            "image_url": image_url,
            "categories": categories,
            "language": self.html_settings.get("language")
        }
        
        return article
    
    def _parse_page_as_article(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """
        Parse the whole page as a single article.
        
        Args:
            soup: BeautifulSoup object representing the page
            url: URL of the page
            
        Returns:
            Article data dictionary or None if invalid
        """
        # Extract title
        title_element = soup.select_one(self.title_selector) or soup.find("title")
        if not title_element:
            return None
        
        title = title_element.get_text().strip()
        if not title:
            return None
        
        # Extract content
        content = None
        content_element = soup.select_one(self.content_selector)
        if content_element:
            content = content_element.get_text().strip()
        
        # Extract summary
        summary = None
        summary_element = soup.select_one(self.summary_selector)
        if summary_element:
            summary = summary_element.get_text().strip()
        
        # Extract meta description as fallback for summary
        if not summary:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.has_attr("content"):
                summary = meta_desc["content"].strip()
        
        # Extract published date
        published_at = None
        date_element = soup.select_one(self.date_selector)
        if date_element:
            date_text = date_element.get_text().strip()
            published_at = self._parse_date(date_text)
        
        # Try to extract date from meta tags if not found
        if not published_at:
            meta_date = soup.find("meta", attrs={"property": "article:published_time"})
            if meta_date and meta_date.has_attr("content"):
                try:
                    published_at = date_parser.parse(meta_date["content"])
                except:
                    pass
        
        # Extract author
        author = None
        author_element = soup.select_one(self.author_selector)
        if author_element:
            author = author_element.get_text().strip()
        
        # Try to extract author from meta tags if not found
        if not author:
            meta_author = soup.find("meta", attrs={"name": "author"})
            if meta_author and meta_author.has_attr("content"):
                author = meta_author["content"].strip()
        
        # Extract image URL
        image_url = None
        image_element = soup.select_one(self.image_selector)
        if image_element and image_element.has_attr("src"):
            image_url = image_element["src"]
            # Resolve relative URLs
            if image_url and not (image_url.startswith("http://") or image_url.startswith("https://")):
                image_url = self._resolve_url(url, image_url)
        
        # Try to extract image from meta tags if not found
        if not image_url:
            meta_image = soup.find("meta", attrs={"property": "og:image"})
            if meta_image and meta_image.has_attr("content"):
                image_url = meta_image["content"]
        
        # Extract categories
        categories = []
        category_elements = soup.select(self.category_selector)
        for category_element in category_elements:
            category = category_element.get_text().strip()
            if category:
                categories.append(category)
        
        # Create article
        article = {
            "title": title,
            "url": url,
            "content": content,
            "summary": summary,
            "published_at": published_at.isoformat() if published_at else None,
            "author": author,
            "image_url": image_url,
            "categories": categories,
            "language": self.html_settings.get("language")
        }
        
        return article
    
    async def _get_next_page_url(self, current_url: str) -> Optional[str]:
        """
        Get the URL of the next page for pagination.
        
        Args:
            current_url: URL of the current page
            
        Returns:
            URL of the next page or None if not found
        """
        try:
            # Fetch HTML content
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": self.user_agent}
                async with session.get(current_url, headers=headers, timeout=self.timeout) as response:
                    if response.status != 200:
                        return None
                    
                    content = await response.text()
            
            # Parse HTML
            soup = BeautifulSoup(content, "html.parser")
            
            # Find next page link
            next_page_element = soup.select_one(self.next_page_selector)
            if next_page_element and next_page_element.has_attr("href"):
                next_url = next_page_element["href"]
                # Resolve relative URLs
                if next_url and not (next_url.startswith("http://") or next_url.startswith("https://")):
                    next_url = self._resolve_url(current_url, next_url)
                return next_url
            
            return None
        except Exception as e:
            logger.error(f"Error getting next page URL for {current_url}: {e}")
            return None
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse a date string into a datetime object.
        
        Args:
            date_text: Date string to parse
            
        Returns:
            Datetime object or None if parsing fails
        """
        if not date_text:
            return None
        
        try:
            # Try to parse with specified format
            if self.date_format:
                return datetime.strptime(date_text, self.date_format)
            
            # Try to extract date with regex
            if self.date_regex:
                match = re.search(self.date_regex, date_text)
                if match:
                    date_text = match.group(1)
            
            # Try to parse with dateutil
            return date_parser.parse(date_text)
        except Exception as e:
            logger.debug(f"Error parsing date '{date_text}': {e}")
            return None
    
    def _resolve_url(self, base_url: str, relative_url: str) -> str:
        """
        Resolve a relative URL against a base URL.
        
        Args:
            base_url: Base URL
            relative_url: Relative URL
            
        Returns:
            Absolute URL
        """
        if relative_url.startswith("//"):
            # Protocol-relative URL
            return f"https:{relative_url}"
        
        if relative_url.startswith("/"):
            # Root-relative URL
            parsed_base = base_url.split("/")
            if len(parsed_base) >= 3:
                return f"{parsed_base[0]}//{parsed_base[2]}{relative_url}"
            return base_url + relative_url
        
        # Path-relative URL
        base_parts = base_url.split("/")
        if len(base_parts) > 3:
            base_url = "/".join(base_parts[:-1]) + "/"
        else:
            if not base_url.endswith("/"):
                base_url += "/"
        
        return base_url + relative_url