"""
Text cleaner component for the News Aggregator processor pipeline.
Cleans and normalizes text content from articles.
"""

import logging
import re
from typing import Dict, Any, Optional
import html
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger(__name__)


class Cleaner:
    """
    Text cleaner component for the processing pipeline.
    Cleans and normalizes text content from articles.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the cleaner component.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Configure cleaning options
        self.remove_html = self.config.get("remove_html", True)
        self.remove_urls = self.config.get("remove_urls", True)
        self.remove_emails = self.config.get("remove_emails", True)
        self.normalize_whitespace = self.config.get("normalize_whitespace", True)
        self.min_content_length = self.config.get("min_content_length", 100)
        self.max_content_length = self.config.get("max_content_length", 100000)
        self.remove_boilerplate = self.config.get("remove_boilerplate", True)
        
        # Configure boilerplate patterns
        self.boilerplate_patterns = self.config.get("boilerplate_patterns", [
            r"Share this article",
            r"Share on (Facebook|Twitter|LinkedIn)",
            r"Follow us on (Facebook|Twitter|LinkedIn)",
            r"Copyright \d{4}",
            r"All rights reserved",
            r"Terms of (Use|Service)",
            r"Privacy Policy",
            r"Subscribe to our newsletter",
            r"Sign up for our newsletter",
            r"Related articles",
            r"You might also like",
            r"Recommended for you",
            r"Advertisement",
            r"Sponsored content",
            r"Click here to subscribe"
        ])
        
        # Compile regular expressions
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.email_pattern = re.compile(r'\S+@\S+\.\S+')
        self.whitespace_pattern = re.compile(r'\s+')
        self.boilerplate_regex = re.compile('|'.join(self.boilerplate_patterns), re.IGNORECASE)
    
    async def process(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an article by cleaning its content.
        
        Args:
            article: Article data dictionary
            
        Returns:
            Processed article data dictionary
        """
        try:
            # Skip if no content
            if not article.get("content"):
                logger.warning(f"No content to clean for article: {article.get('id', 'unknown')}")
                return article
            
            # Clean content
            cleaned_content = self._clean_text(article["content"])
            
            # Update article
            article["content"] = cleaned_content
            article["content_length"] = len(cleaned_content)
            
            # Add cleaning metadata
            if "metadata" not in article:
                article["metadata"] = {}
            
            article["metadata"]["cleaned"] = True
            
            # Check if content is too short
            if len(cleaned_content) < self.min_content_length:
                logger.warning(f"Content too short after cleaning: {len(cleaned_content)} chars")
                article["metadata"]["content_warning"] = "too_short"
            
            # Check if content is too long
            if self.max_content_length > 0 and len(cleaned_content) > self.max_content_length:
                logger.warning(f"Content too long after cleaning: {len(cleaned_content)} chars")
                article["metadata"]["content_warning"] = "too_long"
                
                # Truncate content
                article["content"] = cleaned_content[:self.max_content_length] + "..."
                article["content_length"] = self.max_content_length + 3
            
            # Clean summary if present
            if article.get("summary"):
                article["summary"] = self._clean_text(article["summary"], is_summary=True)
            
            # Clean title if present
            if article.get("title"):
                article["title"] = self._clean_title(article["title"])
            
            return article
        except Exception as e:
            logger.error(f"Error cleaning article: {e}")
            return article
    
    def _clean_text(self, text: str, is_summary: bool = False) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Text to clean
            is_summary: Whether the text is a summary
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags
        if self.remove_html:
            text = self._remove_html_tags(text)
        
        # Remove URLs
        if self.remove_urls:
            text = self.url_pattern.sub('', text)
        
        # Remove email addresses
        if self.remove_emails:
            text = self.email_pattern.sub('', text)
        
        # Remove boilerplate text
        if self.remove_boilerplate and not is_summary:
            text = self.boilerplate_regex.sub('', text)
        
        # Normalize whitespace
        if self.normalize_whitespace:
            text = self._normalize_whitespace(text)
        
        return text.strip()
    
    def _clean_title(self, title: str) -> str:
        """
        Clean and normalize a title.
        
        Args:
            title: Title to clean
            
        Returns:
            Cleaned title
        """
        if not title:
            return ""
        
        # Decode HTML entities
        title = html.unescape(title)
        
        # Remove HTML tags
        title = self._remove_html_tags(title)
        
        # Normalize whitespace
        title = self._normalize_whitespace(title)
        
        return title.strip()
    
    def _remove_html_tags(self, text: str) -> str:
        """
        Remove HTML tags from text.
        
        Args:
            text: Text with HTML tags
            
        Returns:
            Text without HTML tags
        """
        try:
            # Check if text contains HTML
            if "<" in text and ">" in text:
                soup = BeautifulSoup(text, "html.parser")
                return soup.get_text()
            return text
        except Exception as e:
            logger.error(f"Error removing HTML tags: {e}")
            return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Replace multiple whitespace characters with a single space
        text = self.whitespace_pattern.sub(' ', text)
        
        # Replace multiple newlines with a single newline
        text = re.sub(r'\n+', '\n', text)
        
        # Remove spaces at the beginning and end of lines
        text = re.sub(r'^ +| +$', '', text, flags=re.MULTILINE)
        
        return text.strip()