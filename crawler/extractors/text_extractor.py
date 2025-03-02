"""
Text extractor for the News Aggregator crawler.
Extracts and processes text content from articles.
"""

import logging
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import trafilatura
import newspaper
from newspaper import Article as NewspaperArticle
from readability import Document

# Configure logging
logger = logging.getLogger(__name__)


class TextExtractor:
    """
    Text extractor for news articles.
    Extracts and processes text content from HTML.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the text extractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Configure extraction options
        self.min_content_length = self.config.get("min_content_length", 100)
        self.max_content_length = self.config.get("max_content_length", 100000)
        self.extraction_method = self.config.get("extraction_method", "auto")
        self.fallback_methods = self.config.get("fallback_methods", ["trafilatura", "newspaper", "readability", "basic"])
        self.remove_boilerplate = self.config.get("remove_boilerplate", True)
        self.extract_comments = self.config.get("extract_comments", False)
        
        # Configure cleaning options
        self.clean_html = self.config.get("clean_html", True)
        self.normalize_whitespace = self.config.get("normalize_whitespace", True)
        self.remove_ads = self.config.get("remove_ads", True)
        self.remove_links = self.config.get("remove_links", False)
        
        # Configure selectors
        self.content_selectors = self.config.get("content_selectors", [
            "article", ".article", ".post", ".entry", ".content", 
            ".post-content", ".entry-content", ".article-content",
            "#article", "#content", "#post", "#entry"
        ])
        
        # Configure exclusion selectors
        self.exclusion_selectors = self.config.get("exclusion_selectors", [
            ".ad", ".advertisement", ".banner", ".social", ".share", 
            ".comment", ".comments", ".related", ".sidebar", ".widget",
            "nav", "header", "footer", ".header", ".footer", ".nav",
            ".menu", ".navigation", ".recommended", ".popular", ".trending"
        ])
        
        # Ad-related patterns
        self.ad_patterns = self.config.get("ad_patterns", [
            r"Advertisement\s*", r"Sponsored\s*", r"Promoted\s*",
            r"From our sponsors\s*", r"From our advertisers\s*",
            r"From our partners\s*", r"Paid content\s*", r"Paid post\s*"
        ])
    
    async def extract(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and process text content from an article.
        
        Args:
            article: Article data dictionary
            
        Returns:
            Updated article data dictionary
        """
        try:
            # Skip if no URL or content already exists and is sufficient
            if not article.get("url"):
                logger.warning("Cannot extract text: no URL provided")
                return article
            
            # If content already exists and is sufficient, skip extraction
            if article.get("content") and len(article["content"]) >= self.min_content_length:
                # Just clean the existing content
                if self.clean_html:
                    article["content"] = self._clean_html(article["content"])
                if self.normalize_whitespace:
                    article["content"] = self._normalize_whitespace(article["content"])
                if self.remove_ads:
                    article["content"] = self._remove_ad_content(article["content"])
                
                return article
            
            # Get HTML content
            html_content = article.get("html_content")
            
            # If no HTML content, try to use content field
            if not html_content and article.get("content"):
                html_content = article["content"]
            
            # If still no HTML content, return the article as is
            if not html_content:
                logger.warning(f"No HTML content to extract text from for URL: {article.get('url')}")
                return article
            
            # Extract text based on the configured method
            if self.extraction_method == "auto":
                # Try all methods in order until one succeeds
                for method in self.fallback_methods:
                    content = self._extract_with_method(html_content, method, article.get("url"))
                    if content and len(content) >= self.min_content_length:
                        break
            else:
                # Use the specified method
                content = self._extract_with_method(html_content, self.extraction_method, article.get("url"))
            
            # If extraction failed, return the article as is
            if not content or len(content) < self.min_content_length:
                logger.warning(f"Failed to extract meaningful text content from URL: {article.get('url')}")
                return article
            
            # Truncate if too long
            if self.max_content_length > 0 and len(content) > self.max_content_length:
                content = content[:self.max_content_length] + "..."
            
            # Update the article
            article["content"] = content
            
            # Extract summary if not already present
            if not article.get("summary") and content:
                article["summary"] = self._generate_summary(content)
            
            return article
        except Exception as e:
            logger.error(f"Error extracting text from article: {e}")
            return article
    
    def _extract_with_method(self, html_content: str, method: str, url: Optional[str] = None) -> Optional[str]:
        """
        Extract text using a specific method.
        
        Args:
            html_content: HTML content
            method: Extraction method
            url: URL of the article
            
        Returns:
            Extracted text or None if extraction failed
        """
        try:
            if method == "trafilatura":
                return self._extract_with_trafilatura(html_content)
            elif method == "newspaper":
                return self._extract_with_newspaper(html_content, url)
            elif method == "readability":
                return self._extract_with_readability(html_content)
            elif method == "basic":
                return self._extract_with_basic(html_content)
            else:
                logger.warning(f"Unknown extraction method: {method}")
                return None
        except Exception as e:
            logger.error(f"Error extracting text with method {method}: {e}")
            return None
    
    def _extract_with_trafilatura(self, html_content: str) -> Optional[str]:
        """
        Extract text using Trafilatura.
        
        Args:
            html_content: HTML content
            
        Returns:
            Extracted text or None if extraction failed
        """
        try:
            extracted = trafilatura.extract(
                html_content,
                include_comments=self.extract_comments,
                include_links=not self.remove_links,
                include_images=False,
                include_tables=True,
                no_fallback=False
            )
            
            if not extracted:
                return None
            
            # Clean the extracted text
            if self.normalize_whitespace:
                extracted = self._normalize_whitespace(extracted)
            if self.remove_ads:
                extracted = self._remove_ad_content(extracted)
            
            return extracted
        except Exception as e:
            logger.error(f"Error extracting text with Trafilatura: {e}")
            return None
    
    def _extract_with_newspaper(self, html_content: str, url: Optional[str] = None) -> Optional[str]:
        """
        Extract text using Newspaper3k.
        
        Args:
            html_content: HTML content
            url: URL of the article
            
        Returns:
            Extracted text or None if extraction failed
        """
        try:
            article = NewspaperArticle(url=url or "")
            article.set_html(html_content)
            article.parse()
            
            text = article.text
            
            if not text:
                return None
            
            # Clean the extracted text
            if self.normalize_whitespace:
                text = self._normalize_whitespace(text)
            if self.remove_ads:
                text = self._remove_ad_content(text)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text with Newspaper3k: {e}")
            return None
    
    def _extract_with_readability(self, html_content: str) -> Optional[str]:
        """
        Extract text using Readability.
        
        Args:
            html_content: HTML content
            
        Returns:
            Extracted text or None if extraction failed
        """
        try:
            doc = Document(html_content)
            content = doc.summary()
            
            if not content:
                return None
            
            # Clean the HTML
            if self.clean_html:
                content = self._clean_html(content)
            if self.normalize_whitespace:
                content = self._normalize_whitespace(content)
            if self.remove_ads:
                content = self._remove_ad_content(content)
            
            return content
        except Exception as e:
            logger.error(f"Error extracting text with Readability: {e}")
            return None
    
    def _extract_with_basic(self, html_content: str) -> Optional[str]:
        """
        Extract text using basic BeautifulSoup parsing.
        
        Args:
            html_content: HTML content
            
        Returns:
            Extracted text or None if extraction failed
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove script, style, and other non-content elements
            for element in soup(["script", "style", "meta", "noscript", "iframe", "svg"]):
                element.decompose()
            
            # Remove elements matching exclusion selectors
            if self.exclusion_selectors:
                for selector in self.exclusion_selectors:
                    for element in soup.select(selector):
                        element.decompose()
            
            # Try to find the main content element
            content_element = None
            for selector in self.content_selectors:
                elements = soup.select(selector)
                if elements:
                    # Use the largest element by text length
                    content_element = max(elements, key=lambda e: len(e.get_text()))
                    break
            
            # If no content element found, use the body
            if not content_element:
                content_element = soup.body
            
            # If still no content element, use the whole document
            if not content_element:
                content_element = soup
            
            # Extract text
            text = content_element.get_text()
            
            if not text:
                return None
            
            # Clean the extracted text
            if self.normalize_whitespace:
                text = self._normalize_whitespace(text)
            if self.remove_ads:
                text = self._remove_ad_content(text)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text with basic method: {e}")
            return None
    
    def _clean_html(self, html_content: str) -> str:
        """
        Clean HTML content to extract plain text.
        
        Args:
            html_content: HTML content
            
        Returns:
            Cleaned text
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove script, style, and other non-content elements
            for element in soup(["script", "style", "meta", "noscript", "iframe", "svg"]):
                element.decompose()
            
            # Remove elements matching exclusion selectors
            if self.exclusion_selectors:
                for selector in self.exclusion_selectors:
                    for element in soup.select(selector):
                        element.decompose()
            
            # Get text
            text = soup.get_text()
            
            return text
        except Exception as e:
            logger.error(f"Error cleaning HTML: {e}")
            return html_content
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        try:
            # Replace multiple newlines with a single newline
            text = re.sub(r'\n+', '\n', text)
            
            # Replace multiple spaces with a single space
            text = re.sub(r' +', ' ', text)
            
            # Remove spaces at the beginning and end of lines
            text = re.sub(r'^ +| +$', '', text, flags=re.MULTILINE)
            
            # Remove empty lines
            text = re.sub(r'\n+', '\n', text)
            
            # Remove whitespace at the beginning and end of the text
            text = text.strip()
            
            return text
        except Exception as e:
            logger.error(f"Error normalizing whitespace: {e}")
            return text
    
    def _remove_ad_content(self, text: str) -> str:
        """
        Remove advertisement-related content from text.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        try:
            if not self.ad_patterns:
                return text
            
            # Remove ad-related content
            for pattern in self.ad_patterns:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
            return text
        except Exception as e:
            logger.error(f"Error removing ad content: {e}")
            return text
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """
        Generate a summary from the content.
        
        Args:
            content: Content to summarize
            max_length: Maximum length of the summary
            
        Returns:
            Summary
        """
        try:
            # Simple summary generation: take the first paragraph or first few sentences
            paragraphs = content.split('\n')
            
            # Find the first non-empty paragraph
            summary = ""
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if paragraph:
                    summary = paragraph
                    break
            
            # If no paragraph found, use the whole content
            if not summary:
                summary = content
            
            # Truncate if too long
            if len(summary) > max_length:
                # Try to truncate at a sentence boundary
                sentences = re.split(r'(?<=[.!?])\s+', summary[:max_length + 50])
                summary = ' '.join(sentences[:-1])
                
                # If still too long, truncate at max_length
                if len(summary) > max_length:
                    summary = summary[:max_length] + "..."
            
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return content[:max_length] + "..." if len(content) > max_length else content