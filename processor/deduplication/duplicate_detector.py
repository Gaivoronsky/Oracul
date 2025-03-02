"""
Duplicate detector for the News Aggregator processor.
Detects duplicate articles based on content similarity.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Set
import re
from datetime import datetime, timedelta
import hashlib

# Configure logging
logger = logging.getLogger(__name__)


class DuplicateDetector:
    """
    Duplicate detector for the News Aggregator processor.
    Detects duplicate articles based on content similarity.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the duplicate detector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Configure deduplication options
        self.enabled = self.config.get("enabled", True)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.8)
        self.title_weight = self.config.get("title_weight", 0.6)
        self.content_weight = self.config.get("content_weight", 0.4)
        self.max_days_back = self.config.get("max_days_back", 7)
        self.min_content_length = self.config.get("min_content_length", 100)
        self.use_exact_match = self.config.get("use_exact_match", True)
        self.use_fuzzy_match = self.config.get("use_fuzzy_match", True)
        self.use_minhash = self.config.get("use_minhash", False)
        
        # Initialize minhash
        self.minhash_index = None
        
        if self.use_minhash:
            self._initialize_minhash()
    
    def _initialize_minhash(self):
        """
        Initialize MinHash for faster similarity computation.
        """
        try:
            from datasketch import MinHash, MinHashLSH
            
            # Initialize LSH index
            self.minhash_index = MinHashLSH(
                threshold=self.similarity_threshold,
                num_perm=128
            )
            
            logger.info("Initialized MinHash LSH index")
        
        except ImportError:
            logger.warning("datasketch not installed, MinHash deduplication disabled")
            self.use_minhash = False
        
        except Exception as e:
            logger.error(f"Error initializing MinHash: {e}")
            self.use_minhash = False
    
    async def check_duplicate(self, article: Dict[str, Any], repository) -> Tuple[bool, Optional[str]]:
        """
        Check if an article is a duplicate of an existing article.
        
        Args:
            article: Article data dictionary
            repository: Repository for accessing articles
            
        Returns:
            Tuple of (is_duplicate, duplicate_id)
        """
        try:
            # Skip if disabled
            if not self.enabled:
                return False, None
            
            # Skip if no content or title
            if not article.get("content") and not article.get("title"):
                logger.warning(f"No content or title to check for duplicates: {article.get('id', 'unknown')}")
                return False, None
            
            # Skip if content is too short
            if article.get("content") and len(article["content"]) < self.min_content_length and not article.get("title"):
                logger.warning(f"Content too short for duplicate detection: {len(article['content'])} chars")
                return False, None
            
            # Get recent articles
            recent_articles = await self._get_recent_articles(article, repository)
            
            if not recent_articles:
                return False, None
            
            # Check for duplicates
            is_duplicate, duplicate_id = await self._find_duplicate(article, recent_articles)
            
            if is_duplicate:
                logger.info(f"Found duplicate: {article.get('id', 'unknown')} is a duplicate of {duplicate_id}")
            
            return is_duplicate, duplicate_id
        
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return False, None
    
    async def _get_recent_articles(self, article: Dict[str, Any], repository) -> List[Dict[str, Any]]:
        """
        Get recent articles for duplicate detection.
        
        Args:
            article: Article data dictionary
            repository: Repository for accessing articles
            
        Returns:
            List of recent articles
        """
        try:
            # Calculate date range
            max_days_back = self.max_days_back
            
            # Get current date
            current_date = datetime.now()
            
            # Calculate start date
            start_date = current_date - timedelta(days=max_days_back)
            
            # Get articles from repository
            articles = await repository.get_articles(
                start_date=start_date,
                exclude_ids=[article.get("id")] if article.get("id") else None,
                limit=100  # Limit to avoid processing too many articles
            )
            
            return articles
        
        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
            return []
    
    async def _find_duplicate(self, article: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Find a duplicate article among candidates.
        
        Args:
            article: Article data dictionary
            candidates: List of candidate articles
            
        Returns:
            Tuple of (is_duplicate, duplicate_id)
        """
        # Check exact matches
        if self.use_exact_match:
            exact_match, exact_match_id = self._check_exact_match(article, candidates)
            
            if exact_match:
                return True, exact_match_id
        
        # Check MinHash matches
        if self.use_minhash and self.minhash_index:
            minhash_match, minhash_match_id = await self._check_minhash(article, candidates)
            
            if minhash_match:
                return True, minhash_match_id
        
        # Check fuzzy matches
        if self.use_fuzzy_match:
            fuzzy_match, fuzzy_match_id = await self._check_fuzzy_match(article, candidates)
            
            if fuzzy_match:
                return True, fuzzy_match_id
        
        return False, None
    
    def _check_exact_match(self, article: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Check for exact matches based on title and URL.
        
        Args:
            article: Article data dictionary
            candidates: List of candidate articles
            
        Returns:
            Tuple of (is_duplicate, duplicate_id)
        """
        # Get article title and URL
        title = article.get("title", "").strip().lower()
        url = article.get("url", "").strip().lower()
        
        # Skip if no title or URL
        if not title and not url:
            return False, None
        
        # Check candidates
        for candidate in candidates:
            # Check title
            if title and candidate.get("title"):
                candidate_title = candidate["title"].strip().lower()
                
                if title == candidate_title:
                    return True, candidate["id"]
            
            # Check URL
            if url and candidate.get("url"):
                candidate_url = candidate["url"].strip().lower()
                
                if url == candidate_url:
                    return True, candidate["id"]
        
        return False, None
    
    async def _check_minhash(self, article: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Check for duplicates using MinHash LSH.
        
        Args:
            article: Article data dictionary
            candidates: List of candidate articles
            
        Returns:
            Tuple of (is_duplicate, duplicate_id)
        """
        try:
            from datasketch import MinHash
            
            # Get article text
            article_text = self._prepare_text(article)
            
            if not article_text:
                return False, None
            
            # Create MinHash for article
            article_minhash = MinHash(num_perm=128)
            
            # Update MinHash with shingles
            for shingle in self._get_shingles(article_text):
                article_minhash.update(shingle.encode("utf-8"))
            
            # Clear index
            self.minhash_index = self.minhash_index.__class__(
                threshold=self.similarity_threshold,
                num_perm=128
            )
            
            # Add candidates to index
            for candidate in candidates:
                candidate_text = self._prepare_text(candidate)
                
                if not candidate_text:
                    continue
                
                # Create MinHash for candidate
                candidate_minhash = MinHash(num_perm=128)
                
                # Update MinHash with shingles
                for shingle in self._get_shingles(candidate_text):
                    candidate_minhash.update(shingle.encode("utf-8"))
                
                # Add to index
                self.minhash_index.insert(candidate["id"], candidate_minhash)
            
            # Query index
            matches = self.minhash_index.query(article_minhash)
            
            if matches:
                return True, matches[0]
            
            return False, None
        
        except Exception as e:
            logger.error(f"Error checking MinHash: {e}")
            return False, None
    
    async def _check_fuzzy_match(self, article: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Check for fuzzy matches based on content similarity.
        
        Args:
            article: Article data dictionary
            candidates: List of candidate articles
            
        Returns:
            Tuple of (is_duplicate, duplicate_id)
        """
        # Get article title and content
        title = article.get("title", "")
        content = article.get("content", "")
        
        # Skip if no title and no content
        if not title and not content:
            return False, None
        
        # Check candidates
        best_similarity = 0.0
        best_candidate_id = None
        
        for candidate in candidates:
            # Get candidate title and content
            candidate_title = candidate.get("title", "")
            candidate_content = candidate.get("content", "")
            
            # Skip if no title and no content
            if not candidate_title and not candidate_content:
                continue
            
            # Calculate similarity
            similarity = self._calculate_similarity(
                title, content,
                candidate_title, candidate_content
            )
            
            # Check if duplicate
            if similarity > self.similarity_threshold and similarity > best_similarity:
                best_similarity = similarity
                best_candidate_id = candidate["id"]
        
        if best_candidate_id:
            return True, best_candidate_id
        
        return False, None
    
    def _calculate_similarity(self, title1: str, content1: str, title2: str, content2: str) -> float:
        """
        Calculate similarity between two articles.
        
        Args:
            title1: Title of first article
            content1: Content of first article
            title2: Title of second article
            content2: Content of second article
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Calculate title similarity
        title_similarity = 0.0
        
        if title1 and title2:
            title_similarity = self._calculate_text_similarity(title1, title2)
        
        # Calculate content similarity
        content_similarity = 0.0
        
        if content1 and content2:
            content_similarity = self._calculate_text_similarity(content1, content2)
        
        # Calculate weighted similarity
        if title1 and title2 and content1 and content2:
            # Use both title and content
            similarity = (
                title_similarity * self.title_weight +
                content_similarity * self.content_weight
            )
        elif title1 and title2:
            # Use only title
            similarity = title_similarity
        elif content1 and content2:
            # Use only content
            similarity = content_similarity
        else:
            # No similarity
            similarity = 0.0
        
        return similarity
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Clean texts
        text1 = self._clean_text(text1)
        text2 = self._clean_text(text2)
        
        # Skip if either text is empty
        if not text1 or not text2:
            return 0.0
        
        # Get sets of words
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        # Skip if either set is empty
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _prepare_text(self, article: Dict[str, Any]) -> str:
        """
        Prepare text for similarity calculation.
        
        Args:
            article: Article data dictionary
            
        Returns:
            Prepared text
        """
        # Get title and content
        title = article.get("title", "")
        content = article.get("content", "")
        
        # Combine title and content
        if title and content:
            # Add title multiple times to give it more weight
            text = title + " " + title + " " + content
        elif title:
            text = title
        elif content:
            text = content
        else:
            return ""
        
        # Clean text
        text = self._clean_text(text)
        
        return text
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text for similarity calculation.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+\.\S+', '', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove numbers
        text = re.sub(r'\d+', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _get_shingles(self, text: str, k: int = 3) -> Set[str]:
        """
        Get k-shingles from text.
        
        Args:
            text: Text to get shingles from
            k: Size of shingles
            
        Returns:
            Set of shingles
        """
        words = text.split()
        
        if len(words) < k:
            return {" ".join(words)}
        
        return {" ".join(words[i:i+k]) for i in range(len(words) - k + 1)}
    
    def _get_text_hash(self, text: str) -> str:
        """
        Get hash of text.
        
        Args:
            text: Text to hash
            
        Returns:
            Hash of text
        """
        return hashlib.md5(text.encode("utf-8")).hexdigest()