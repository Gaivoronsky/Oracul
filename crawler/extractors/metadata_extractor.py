"""
Metadata extractor for the News Aggregator crawler.
Extracts metadata from articles such as title, author, publication date, etc.
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import newspaper
from newspaper import Article as NewspaperArticle
from dateutil import parser as date_parser

# Configure logging
logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Metadata extractor for news articles.
    Extracts metadata such as title, author, publication date, etc.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the metadata extractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Configure extraction options
        self.extraction_method = self.config.get("extraction_method", "auto")
        self.fallback_methods = self.config.get("fallback_methods", ["newspaper", "opengraph", "meta", "json_ld", "basic"])
        
        # Configure selectors
        self.selectors = self.config.get("selectors", {})
        self.title_selectors = self.selectors.get("title", [
            "h1.title", "h1.headline", "h1.article-title", ".article-title", ".post-title",
            ".entry-title", "h1", "title"
        ])
        self.author_selectors = self.selectors.get("author", [
            ".author", ".byline", ".article-author", ".post-author", ".entry-author",
            "meta[name='author']", "meta[property='article:author']"
        ])
        self.date_selectors = self.selectors.get("date", [
            ".date", ".time", ".published", ".timestamp", ".article-date", ".post-date",
            "time", "meta[name='date']", "meta[property='article:published_time']"
        ])
        self.description_selectors = self.selectors.get("description", [
            ".description", ".summary", ".article-summary", ".post-summary", ".entry-summary",
            "meta[name='description']", "meta[property='og:description']"
        ])
        self.image_selectors = self.selectors.get("image", [
            ".featured-image img", ".article-image img", ".post-image img", ".entry-image img",
            "meta[property='og:image']", "meta[name='twitter:image']"
        ])
        self.category_selectors = self.selectors.get("category", [
            ".category", ".categories", ".tags", ".article-category", ".post-category",
            "meta[property='article:section']", "meta[name='keywords']"
        ])
        
        # Date parsing
        self.date_formats = self.config.get("date_formats", [
            "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y",
            "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y",
            "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"
        ])
        self.date_regexes = self.config.get("date_regexes", [
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))",  # ISO 8601
            r"(\d{4}-\d{2}-\d{2})",  # YYYY-MM-DD
            r"(\d{2}/\d{2}/\d{4})",  # DD/MM/YYYY
            r"(\w+ \d{1,2}, \d{4})"   # Month DD, YYYY
        ])
    
    async def extract(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from an article.
        
        Args:
            article: Article data dictionary
            
        Returns:
            Updated article data dictionary
        """
        try:
            # Skip if no URL
            if not article.get("url"):
                logger.warning("Cannot extract metadata: no URL provided")
                return article
            
            # Get HTML content
            html_content = article.get("html_content")
            
            # If no HTML content, return the article as is
            if not html_content:
                logger.warning(f"No HTML content to extract metadata from for URL: {article.get('url')}")
                return article
            
            # Extract metadata based on the configured method
            if self.extraction_method == "auto":
                # Try all methods in order until all metadata is extracted
                for method in self.fallback_methods:
                    article = self._extract_with_method(article, html_content, method)
                    
                    # Check if all metadata is extracted
                    if self._is_metadata_complete(article):
                        break
            else:
                # Use the specified method
                article = self._extract_with_method(article, html_content, self.extraction_method)
            
            return article
        except Exception as e:
            logger.error(f"Error extracting metadata from article: {e}")
            return article
    
    def _extract_with_method(self, article: Dict[str, Any], html_content: str, method: str) -> Dict[str, Any]:
        """
        Extract metadata using a specific method.
        
        Args:
            article: Article data dictionary
            html_content: HTML content
            method: Extraction method
            
        Returns:
            Updated article data dictionary
        """
        try:
            if method == "newspaper":
                return self._extract_with_newspaper(article, html_content)
            elif method == "opengraph":
                return self._extract_opengraph(article, html_content)
            elif method == "meta":
                return self._extract_meta_tags(article, html_content)
            elif method == "json_ld":
                return self._extract_json_ld(article, html_content)
            elif method == "basic":
                return self._extract_with_basic(article, html_content)
            else:
                logger.warning(f"Unknown metadata extraction method: {method}")
                return article
        except Exception as e:
            logger.error(f"Error extracting metadata with method {method}: {e}")
            return article
    
    def _extract_with_newspaper(self, article: Dict[str, Any], html_content: str) -> Dict[str, Any]:
        """
        Extract metadata using Newspaper3k.
        
        Args:
            article: Article data dictionary
            html_content: HTML content
            
        Returns:
            Updated article data dictionary
        """
        try:
            # Create a newspaper Article object
            news_article = NewspaperArticle(url=article.get("url", ""))
            news_article.set_html(html_content)
            news_article.parse()
            
            # Extract title if not already present
            if not article.get("title") and news_article.title:
                article["title"] = news_article.title
            
            # Extract authors if not already present
            if not article.get("author") and news_article.authors:
                article["author"] = ", ".join(news_article.authors)
            
            # Extract published date if not already present
            if not article.get("published_at") and news_article.publish_date:
                article["published_at"] = news_article.publish_date.isoformat()
            
            # Extract summary if not already present
            if not article.get("summary") and news_article.meta_description:
                article["summary"] = news_article.meta_description
            
            # Extract image URL if not already present
            if not article.get("image_url") and news_article.top_image:
                article["image_url"] = news_article.top_image
            
            # Extract keywords/categories if not already present
            if not article.get("categories") and news_article.meta_keywords:
                article["categories"] = news_article.meta_keywords
            
            return article
        except Exception as e:
            logger.error(f"Error extracting metadata with Newspaper3k: {e}")
            return article
    
    def _extract_opengraph(self, article: Dict[str, Any], html_content: str) -> Dict[str, Any]:
        """
        Extract metadata from OpenGraph tags.
        
        Args:
            article: Article data dictionary
            html_content: HTML content
            
        Returns:
            Updated article data dictionary
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract title if not already present
            if not article.get("title"):
                og_title = soup.find("meta", property="og:title")
                if og_title and og_title.get("content"):
                    article["title"] = og_title["content"]
            
            # Extract description/summary if not already present
            if not article.get("summary"):
                og_desc = soup.find("meta", property="og:description")
                if og_desc and og_desc.get("content"):
                    article["summary"] = og_desc["content"]
            
            # Extract image URL if not already present
            if not article.get("image_url"):
                og_image = soup.find("meta", property="og:image")
                if og_image and og_image.get("content"):
                    article["image_url"] = og_image["content"]
            
            # Extract published date if not already present
            if not article.get("published_at"):
                og_date = soup.find("meta", property="article:published_time")
                if og_date and og_date.get("content"):
                    try:
                        dt = date_parser.parse(og_date["content"])
                        article["published_at"] = dt.isoformat()
                    except:
                        pass
            
            # Extract author if not already present
            if not article.get("author"):
                og_author = soup.find("meta", property="article:author")
                if og_author and og_author.get("content"):
                    article["author"] = og_author["content"]
            
            # Extract categories if not already present
            if not article.get("categories"):
                categories = []
                og_section = soup.find("meta", property="article:section")
                if og_section and og_section.get("content"):
                    categories.append(og_section["content"])
                
                og_tags = soup.find_all("meta", property="article:tag")
                for tag in og_tags:
                    if tag.get("content"):
                        categories.append(tag["content"])
                
                if categories:
                    article["categories"] = categories
            
            return article
        except Exception as e:
            logger.error(f"Error extracting OpenGraph metadata: {e}")
            return article
    
    def _extract_meta_tags(self, article: Dict[str, Any], html_content: str) -> Dict[str, Any]:
        """
        Extract metadata from standard meta tags.
        
        Args:
            article: Article data dictionary
            html_content: HTML content
            
        Returns:
            Updated article data dictionary
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract title if not already present
            if not article.get("title"):
                meta_title = soup.find("meta", attrs={"name": "title"})
                if meta_title and meta_title.get("content"):
                    article["title"] = meta_title["content"]
                else:
                    title_tag = soup.find("title")
                    if title_tag:
                        article["title"] = title_tag.get_text()
            
            # Extract description/summary if not already present
            if not article.get("summary"):
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc and meta_desc.get("content"):
                    article["summary"] = meta_desc["content"]
            
            # Extract author if not already present
            if not article.get("author"):
                meta_author = soup.find("meta", attrs={"name": "author"})
                if meta_author and meta_author.get("content"):
                    article["author"] = meta_author["content"]
            
            # Extract published date if not already present
            if not article.get("published_at"):
                meta_date = soup.find("meta", attrs={"name": "date"})
                if meta_date and meta_date.get("content"):
                    try:
                        dt = date_parser.parse(meta_date["content"])
                        article["published_at"] = dt.isoformat()
                    except:
                        pass
            
            # Extract keywords/categories if not already present
            if not article.get("categories"):
                meta_keywords = soup.find("meta", attrs={"name": "keywords"})
                if meta_keywords and meta_keywords.get("content"):
                    keywords = [k.strip() for k in meta_keywords["content"].split(",")]
                    article["categories"] = keywords
            
            return article
        except Exception as e:
            logger.error(f"Error extracting meta tag metadata: {e}")
            return article
    
    def _extract_json_ld(self, article: Dict[str, Any], html_content: str) -> Dict[str, Any]:
        """
        Extract metadata from JSON-LD structured data.
        
        Args:
            article: Article data dictionary
            html_content: HTML content
            
        Returns:
            Updated article data dictionary
        """
        try:
            import json
            from jsonpath_ng import parse
            
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Find JSON-LD scripts
            json_ld_scripts = soup.find_all("script", type="application/ld+json")
            
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    
                    # Check if it's an Article or NewsArticle
                    if isinstance(data, dict):
                        # Extract type
                        type_path = parse("$.['@type']")
                        types = [match.value for match in type_path.find(data)]
                        
                        # Check if it's a relevant type
                        relevant_types = ["Article", "NewsArticle", "BlogPosting", "WebPage"]
                        if not any(t in relevant_types for t in types):
                            continue
                        
                        # Extract title if not already present
                        if not article.get("title"):
                            title_path = parse("$.headline")
                            title_matches = title_path.find(data)
                            if title_matches:
                                article["title"] = title_matches[0].value
                        
                        # Extract author if not already present
                        if not article.get("author"):
                            # Try different author paths
                            author_paths = [
                                parse("$.author.name"),
                                parse("$.author[*].name"),
                                parse("$.author")
                            ]
                            
                            for path in author_paths:
                                author_matches = path.find(data)
                                if author_matches:
                                    if isinstance(author_matches[0].value, list):
                                        authors = [a.get("name", a) for a in author_matches[0].value if a]
                                        article["author"] = ", ".join(authors)
                                    else:
                                        article["author"] = author_matches[0].value
                                    break
                        
                        # Extract published date if not already present
                        if not article.get("published_at"):
                            date_paths = [
                                parse("$.datePublished"),
                                parse("$.dateCreated"),
                                parse("$.dateModified")
                            ]
                            
                            for path in date_paths:
                                date_matches = path.find(data)
                                if date_matches:
                                    try:
                                        dt = date_parser.parse(date_matches[0].value)
                                        article["published_at"] = dt.isoformat()
                                        break
                                    except:
                                        pass
                        
                        # Extract description/summary if not already present
                        if not article.get("summary"):
                            desc_path = parse("$.description")
                            desc_matches = desc_path.find(data)
                            if desc_matches:
                                article["summary"] = desc_matches[0].value
                        
                        # Extract image URL if not already present
                        if not article.get("image_url"):
                            image_paths = [
                                parse("$.image.url"),
                                parse("$.image")
                            ]
                            
                            for path in image_paths:
                                image_matches = path.find(data)
                                if image_matches:
                                    if isinstance(image_matches[0].value, dict) and "url" in image_matches[0].value:
                                        article["image_url"] = image_matches[0].value["url"]
                                    else:
                                        article["image_url"] = image_matches[0].value
                                    break
                        
                        # Extract categories if not already present
                        if not article.get("categories"):
                            category_paths = [
                                parse("$.keywords"),
                                parse("$.articleSection"),
                                parse("$.about[*].name")
                            ]
                            
                            for path in category_paths:
                                category_matches = path.find(data)
                                if category_matches:
                                    if isinstance(category_matches[0].value, str):
                                        categories = [c.strip() for c in category_matches[0].value.split(",")]
                                        article["categories"] = categories
                                    elif isinstance(category_matches[0].value, list):
                                        article["categories"] = category_matches[0].value
                                    break
                
                except Exception as e:
                    logger.error(f"Error parsing JSON-LD script: {e}")
                    continue
            
            return article
        except Exception as e:
            logger.error(f"Error extracting JSON-LD metadata: {e}")
            return article
    
    def _extract_with_basic(self, article: Dict[str, Any], html_content: str) -> Dict[str, Any]:
        """
        Extract metadata using basic HTML parsing with selectors.
        
        Args:
            article: Article data dictionary
            html_content: HTML content
            
        Returns:
            Updated article data dictionary
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract title if not already present
            if not article.get("title"):
                for selector in self.title_selectors:
                    title_element = soup.select_one(selector)
                    if title_element:
                        if selector == "meta[name='title']" or selector == "meta[property='og:title']":
                            if title_element.get("content"):
                                article["title"] = title_element["content"]
                                break
                        else:
                            title = title_element.get_text().strip()
                            if title:
                                article["title"] = title
                                break
            
            # Extract author if not already present
            if not article.get("author"):
                for selector in self.author_selectors:
                    author_element = soup.select_one(selector)
                    if author_element:
                        if selector.startswith("meta"):
                            if author_element.get("content"):
                                article["author"] = author_element["content"]
                                break
                        else:
                            author = author_element.get_text().strip()
                            if author:
                                article["author"] = author
                                break
            
            # Extract published date if not already present
            if not article.get("published_at"):
                # Try selectors
                for selector in self.date_selectors:
                    date_element = soup.select_one(selector)
                    if date_element:
                        if selector.startswith("meta"):
                            if date_element.get("content"):
                                date_text = date_element["content"]
                        else:
                            date_text = date_element.get_text().strip()
                            
                            # Check for datetime attribute
                            if date_element.name == "time" and date_element.get("datetime"):
                                date_text = date_element["datetime"]
                        
                        if date_text:
                            published_at = self._parse_date(date_text)
                            if published_at:
                                article["published_at"] = published_at.isoformat()
                                break
                
                # If still not found, try to find date in the text
                if not article.get("published_at"):
                    for regex in self.date_regexes:
                        match = re.search(regex, html_content)
                        if match:
                            date_text = match.group(1)
                            published_at = self._parse_date(date_text)
                            if published_at:
                                article["published_at"] = published_at.isoformat()
                                break
            
            # Extract description/summary if not already present
            if not article.get("summary"):
                for selector in self.description_selectors:
                    desc_element = soup.select_one(selector)
                    if desc_element:
                        if selector.startswith("meta"):
                            if desc_element.get("content"):
                                article["summary"] = desc_element["content"]
                                break
                        else:
                            summary = desc_element.get_text().strip()
                            if summary:
                                article["summary"] = summary
                                break
            
            # Extract image URL if not already present
            if not article.get("image_url"):
                for selector in self.image_selectors:
                    image_element = soup.select_one(selector)
                    if image_element:
                        if selector.startswith("meta"):
                            if image_element.get("content"):
                                article["image_url"] = image_element["content"]
                                break
                        else:
                            if image_element.get("src"):
                                article["image_url"] = image_element["src"]
                                break
            
            # Extract categories if not already present
            if not article.get("categories"):
                categories = []
                for selector in self.category_selectors:
                    category_elements = soup.select(selector)
                    if category_elements:
                        if selector.startswith("meta"):
                            for element in category_elements:
                                if element.get("content"):
                                    if "," in element["content"]:
                                        cats = [c.strip() for c in element["content"].split(",")]
                                        categories.extend(cats)
                                    else:
                                        categories.append(element["content"])
                        else:
                            for element in category_elements:
                                category = element.get_text().strip()
                                if category:
                                    categories.append(category)
                
                if categories:
                    article["categories"] = categories
            
            return article
        except Exception as e:
            logger.error(f"Error extracting metadata with basic method: {e}")
            return article
    
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
            # Try to parse with dateutil
            return date_parser.parse(date_text)
        except:
            # Try to parse with specified formats
            for date_format in self.date_formats:
                try:
                    return datetime.strptime(date_text, date_format)
                except:
                    pass
            
            return None
    
    def _is_metadata_complete(self, article: Dict[str, Any]) -> bool:
        """
        Check if all metadata fields are present.
        
        Args:
            article: Article data dictionary
            
        Returns:
            True if all metadata fields are present, False otherwise
        """
        required_fields = ["title", "published_at", "author", "summary", "image_url", "categories"]
        return all(article.get(field) for field in required_fields)