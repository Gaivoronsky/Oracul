"""
Media extractor for the News Aggregator crawler.
Extracts media content from articles such as images, videos, etc.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger(__name__)


class MediaExtractor:
    """
    Media extractor for news articles.
    Extracts media content such as images, videos, etc.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the media extractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Configure extraction options
        self.extract_images = self.config.get("extract_images", True)
        self.extract_videos = self.config.get("extract_videos", True)
        self.extract_audio = self.config.get("extract_audio", True)
        self.max_images = self.config.get("max_images", 10)
        self.min_image_width = self.config.get("min_image_width", 200)
        self.min_image_height = self.config.get("min_image_height", 200)
        self.prefer_high_res = self.config.get("prefer_high_res", True)
        
        # Configure selectors
        self.selectors = self.config.get("selectors", {})
        self.image_selectors = self.selectors.get("images", [
            "img", ".featured-image img", ".article-image img", ".post-image img",
            "meta[property='og:image']", "meta[name='twitter:image']"
        ])
        self.video_selectors = self.selectors.get("videos", [
            "video", "iframe[src*='youtube.com']", "iframe[src*='vimeo.com']",
            "iframe[src*='dailymotion.com']", "iframe[src*='facebook.com/plugins/video']",
            "meta[property='og:video']", "meta[name='twitter:player']"
        ])
        self.audio_selectors = self.selectors.get("audio", [
            "audio", "iframe[src*='soundcloud.com']", "iframe[src*='spotify.com']",
            "iframe[src*='apple.com/apple-music']"
        ])
        
        # Configure exclusion patterns
        self.excluded_image_patterns = self.config.get("excluded_image_patterns", [
            r".*/(avatar|profile|user|icon|logo|banner|ad|advertisement|pixel|tracking|spacer|blank|transparent)\.(jpg|jpeg|png|gif|webp)$",
            r".*/emoji/.*\.(jpg|jpeg|png|gif|webp)$",
            r".*/share/.*\.(jpg|jpeg|png|gif|webp)$",
            r".*/button/.*\.(jpg|jpeg|png|gif|webp)$",
            r".*/badge/.*\.(jpg|jpeg|png|gif|webp)$"
        ])
        
        # Configure image size detection
        self.detect_image_size = self.config.get("detect_image_size", True)
        self.image_size_attrs = self.config.get("image_size_attrs", ["width", "height", "data-width", "data-height"])
    
    async def extract(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract media content from an article.
        
        Args:
            article: Article data dictionary
            
        Returns:
            Updated article data dictionary
        """
        try:
            # Skip if no URL or HTML content
            if not article.get("url") or not article.get("html_content"):
                return article
            
            # Initialize media collections if not present
            if "media" not in article:
                article["media"] = {
                    "images": [],
                    "videos": [],
                    "audio": []
                }
            
            # Get HTML content
            html_content = article["html_content"]
            base_url = article["url"]
            
            # Parse HTML
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract media content
            if self.extract_images:
                images = self._extract_images(soup, base_url)
                if images:
                    article["media"]["images"] = images
                    
                    # Set main image URL if not already present
                    if not article.get("image_url") and images:
                        article["image_url"] = images[0]["url"]
            
            if self.extract_videos:
                videos = self._extract_videos(soup, base_url)
                if videos:
                    article["media"]["videos"] = videos
            
            if self.extract_audio:
                audio = self._extract_audio(soup, base_url)
                if audio:
                    article["media"]["audio"] = audio
            
            return article
        except Exception as e:
            logger.error(f"Error extracting media from article: {e}")
            return article
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extract images from HTML content.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of image dictionaries
        """
        try:
            images = []
            seen_urls = set()
            
            # Extract images using selectors
            for selector in self.image_selectors:
                elements = soup.select(selector)
                
                for element in elements:
                    try:
                        image_url = None
                        alt_text = None
                        caption = None
                        width = None
                        height = None
                        
                        # Extract URL based on element type
                        if element.name == "img":
                            image_url = element.get("src") or element.get("data-src") or element.get("data-lazy-src")
                            alt_text = element.get("alt", "")
                            
                            # Try to get caption from parent figure
                            parent_figure = element.find_parent("figure")
                            if parent_figure:
                                figcaption = parent_figure.find("figcaption")
                                if figcaption:
                                    caption = figcaption.get_text().strip()
                            
                            # Get image dimensions
                            if self.detect_image_size:
                                for attr in self.image_size_attrs:
                                    if element.has_attr(attr):
                                        try:
                                            value = int(element[attr])
                                            if attr in ["width", "data-width"]:
                                                width = value
                                            elif attr in ["height", "data-height"]:
                                                height = value
                                        except:
                                            pass
                        
                        elif element.name == "meta":
                            image_url = element.get("content")
                        
                        # Skip if no URL found
                        if not image_url:
                            continue
                        
                        # Resolve relative URL
                        image_url = urljoin(base_url, image_url)
                        
                        # Skip if already seen
                        if image_url in seen_urls:
                            continue
                        
                        # Skip if matches exclusion patterns
                        if any(re.match(pattern, image_url, re.IGNORECASE) for pattern in self.excluded_image_patterns):
                            continue
                        
                        # Skip if too small (if dimensions are known)
                        if width and height and (width < self.min_image_width or height < self.min_image_height):
                            continue
                        
                        # Add to list
                        image = {
                            "url": image_url,
                            "type": "image"
                        }
                        
                        if alt_text:
                            image["alt_text"] = alt_text
                        
                        if caption:
                            image["caption"] = caption
                        
                        if width:
                            image["width"] = width
                        
                        if height:
                            image["height"] = height
                        
                        images.append(image)
                        seen_urls.add(image_url)
                        
                        # Stop if we've reached the maximum number of images
                        if len(images) >= self.max_images:
                            break
                    
                    except Exception as e:
                        logger.error(f"Error extracting image: {e}")
                
                # Stop if we've reached the maximum number of images
                if len(images) >= self.max_images:
                    break
            
            # Sort images by size (if dimensions are known)
            if self.prefer_high_res:
                images.sort(key=lambda img: (img.get("width", 0) * img.get("height", 0)), reverse=True)
            
            return images
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return []
    
    def _extract_videos(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extract videos from HTML content.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of video dictionaries
        """
        try:
            videos = []
            seen_urls = set()
            
            # Extract videos using selectors
            for selector in self.video_selectors:
                elements = soup.select(selector)
                
                for element in elements:
                    try:
                        video_url = None
                        video_type = None
                        width = None
                        height = None
                        thumbnail = None
                        
                        # Extract URL and type based on element type
                        if element.name == "video":
                            # HTML5 video
                            video_url = element.get("src")
                            
                            # If no src, try to get from source elements
                            if not video_url:
                                source = element.find("source")
                                if source:
                                    video_url = source.get("src")
                            
                            video_type = "html5"
                            
                            # Get dimensions
                            width = element.get("width")
                            height = element.get("height")
                            
                            # Get poster as thumbnail
                            thumbnail = element.get("poster")
                        
                        elif element.name == "iframe":
                            # Embedded video
                            video_url = element.get("src")
                            
                            # Determine type based on URL
                            if "youtube.com" in video_url or "youtu.be" in video_url:
                                video_type = "youtube"
                                # Extract video ID
                                if "youtube.com/embed/" in video_url:
                                    video_id = video_url.split("/embed/")[1].split("?")[0]
                                    thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                            elif "vimeo.com" in video_url:
                                video_type = "vimeo"
                            elif "dailymotion.com" in video_url:
                                video_type = "dailymotion"
                            elif "facebook.com" in video_url:
                                video_type = "facebook"
                            else:
                                video_type = "embed"
                            
                            # Get dimensions
                            width = element.get("width")
                            height = element.get("height")
                        
                        elif element.name == "meta":
                            # Meta tag video
                            video_url = element.get("content")
                            video_type = "meta"
                        
                        # Skip if no URL found
                        if not video_url:
                            continue
                        
                        # Resolve relative URL
                        video_url = urljoin(base_url, video_url)
                        
                        # Skip if already seen
                        if video_url in seen_urls:
                            continue
                        
                        # Add to list
                        video = {
                            "url": video_url,
                            "type": f"video/{video_type}"
                        }
                        
                        if width:
                            try:
                                video["width"] = int(width)
                            except:
                                pass
                        
                        if height:
                            try:
                                video["height"] = int(height)
                            except:
                                pass
                        
                        if thumbnail:
                            video["thumbnail"] = urljoin(base_url, thumbnail)
                        
                        videos.append(video)
                        seen_urls.add(video_url)
                    
                    except Exception as e:
                        logger.error(f"Error extracting video: {e}")
            
            return videos
        except Exception as e:
            logger.error(f"Error extracting videos: {e}")
            return []
    
    def _extract_audio(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extract audio from HTML content.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of audio dictionaries
        """
        try:
            audio_files = []
            seen_urls = set()
            
            # Extract audio using selectors
            for selector in self.audio_selectors:
                elements = soup.select(selector)
                
                for element in elements:
                    try:
                        audio_url = None
                        audio_type = None
                        
                        # Extract URL and type based on element type
                        if element.name == "audio":
                            # HTML5 audio
                            audio_url = element.get("src")
                            
                            # If no src, try to get from source elements
                            if not audio_url:
                                source = element.find("source")
                                if source:
                                    audio_url = source.get("src")
                            
                            audio_type = "html5"
                        
                        elif element.name == "iframe":
                            # Embedded audio
                            audio_url = element.get("src")
                            
                            # Determine type based on URL
                            if "soundcloud.com" in audio_url:
                                audio_type = "soundcloud"
                            elif "spotify.com" in audio_url:
                                audio_type = "spotify"
                            elif "apple.com" in audio_url:
                                audio_type = "apple-music"
                            else:
                                audio_type = "embed"
                        
                        # Skip if no URL found
                        if not audio_url:
                            continue
                        
                        # Resolve relative URL
                        audio_url = urljoin(base_url, audio_url)
                        
                        # Skip if already seen
                        if audio_url in seen_urls:
                            continue
                        
                        # Add to list
                        audio = {
                            "url": audio_url,
                            "type": f"audio/{audio_type}"
                        }
                        
                        audio_files.append(audio)
                        seen_urls.add(audio_url)
                    
                    except Exception as e:
                        logger.error(f"Error extracting audio: {e}")
            
            return audio_files
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return []
    
    def _is_valid_image_url(self, url: str) -> bool:
        """
        Check if an image URL is valid.
        
        Args:
            url: Image URL
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if URL is absolute
            if not urlparse(url).netloc:
                return False
            
            # Check if URL has an image extension
            image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]
            if not any(url.lower().endswith(ext) for ext in image_extensions):
                # Check if URL contains image-related paths
                image_paths = ["/images/", "/img/", "/photos/", "/uploads/"]
                if not any(path in url.lower() for path in image_paths):
                    return False
            
            # Check if URL matches exclusion patterns
            if any(re.match(pattern, url, re.IGNORECASE) for pattern in self.excluded_image_patterns):
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating image URL: {e}")
            return False