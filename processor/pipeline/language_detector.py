"""
Language detector component for the News Aggregator processor pipeline.
Detects the language of article content.
"""

import logging
from typing import Dict, Any, Optional, Tuple
import re

# Configure logging
logger = logging.getLogger(__name__)


class LanguageDetector:
    """
    Language detector component for the processing pipeline.
    Detects the language of article content.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the language detector component.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Configure detection options
        self.default_language = self.config.get("default_language", "en")
        self.min_confidence = self.config.get("min_confidence", 0.5)
        self.min_content_length = self.config.get("min_content_length", 50)
        self.use_metadata = self.config.get("use_metadata", True)
        self.use_langdetect = self.config.get("use_langdetect", True)
        self.use_fasttext = self.config.get("use_fasttext", False)
        self.use_langid = self.config.get("use_langid", False)
        
        # Initialize language detection models
        self.langdetect_model = None
        self.fasttext_model = None
        self.langid_model = None
        
        if self.use_langdetect:
            self._initialize_langdetect()
        
        if self.use_fasttext:
            self._initialize_fasttext()
        
        if self.use_langid:
            self._initialize_langid()
    
    def _initialize_langdetect(self):
        """
        Initialize the langdetect model.
        """
        try:
            import langdetect
            from langdetect import DetectorFactory
            
            # Set seed for deterministic results
            DetectorFactory.seed = 0
            
            self.langdetect_model = True
            logger.info("Initialized langdetect model")
        except ImportError:
            logger.warning("langdetect not installed, falling back to other methods")
            self.use_langdetect = False
    
    def _initialize_fasttext(self):
        """
        Initialize the fasttext model.
        """
        try:
            import fasttext
            
            # Load pre-trained model
            model_path = self.config.get("fasttext_model_path", "models/lid.176.bin")
            self.fasttext_model = fasttext.load_model(model_path)
            
            logger.info(f"Initialized fasttext model from {model_path}")
        except ImportError:
            logger.warning("fasttext not installed, falling back to other methods")
            self.use_fasttext = False
        except Exception as e:
            logger.error(f"Error loading fasttext model: {e}")
            self.use_fasttext = False
    
    def _initialize_langid(self):
        """
        Initialize the langid model.
        """
        try:
            import langid
            
            self.langid_model = langid
            logger.info("Initialized langid model")
        except ImportError:
            logger.warning("langid not installed, falling back to other methods")
            self.use_langid = False
    
    async def process(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an article by detecting its language.
        
        Args:
            article: Article data dictionary
            
        Returns:
            Processed article data dictionary
        """
        try:
            # Skip if language is already set and we trust metadata
            if self.use_metadata and article.get("language"):
                logger.info(f"Using metadata language: {article['language']}")
                return article
            
            # Skip if no content
            if not article.get("content"):
                logger.warning(f"No content to detect language for article: {article.get('id', 'unknown')}")
                article["language"] = self.default_language
                return article
            
            # Skip if content is too short
            if len(article["content"]) < self.min_content_length:
                logger.warning(f"Content too short for language detection: {len(article['content'])} chars")
                article["language"] = self.default_language
                return article
            
            # Detect language
            language, confidence = await self._detect_language(article["content"])
            
            # Update article
            article["language"] = language
            
            # Add language metadata
            if "metadata" not in article:
                article["metadata"] = {}
            
            article["metadata"]["language_confidence"] = confidence
            
            # Log detection
            logger.info(f"Detected language: {language} with confidence: {confidence}")
            
            return article
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            article["language"] = self.default_language
            return article
    
    async def _detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of a text.
        
        Args:
            text: Text to detect language for
            
        Returns:
            Tuple of (language code, confidence)
        """
        results = []
        
        # Clean text for better detection
        text = self._clean_text_for_detection(text)
        
        # Detect with langdetect
        if self.use_langdetect:
            try:
                import langdetect
                
                # Detect language
                detection = langdetect.detect_langs(text)
                
                # Get top result
                if detection:
                    lang = detection[0].lang
                    prob = detection[0].prob
                    results.append((lang, prob, "langdetect"))
            except Exception as e:
                logger.error(f"Error detecting language with langdetect: {e}")
        
        # Detect with fasttext
        if self.use_fasttext and self.fasttext_model:
            try:
                # Predict language
                predictions = self.fasttext_model.predict(text, k=1)
                
                # Get top result
                if predictions and len(predictions) == 2:
                    labels, probs = predictions
                    
                    if labels and probs:
                        # Extract language code from label (format: __label__en)
                        lang = labels[0].replace("__label__", "")
                        prob = probs[0]
                        results.append((lang, prob, "fasttext"))
            except Exception as e:
                logger.error(f"Error detecting language with fasttext: {e}")
        
        # Detect with langid
        if self.use_langid and self.langid_model:
            try:
                # Predict language
                lang, prob = self.langid_model.classify(text)
                
                if lang and prob:
                    results.append((lang, prob, "langid"))
            except Exception as e:
                logger.error(f"Error detecting language with langid: {e}")
        
        # If no results, return default language
        if not results:
            return self.default_language, 0.0
        
        # Sort results by confidence
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Get top result
        top_lang, top_prob, method = results[0]
        
        # If confidence is too low, use default language
        if top_prob < self.min_confidence:
            logger.warning(f"Language detection confidence too low: {top_prob} < {self.min_confidence}")
            return self.default_language, top_prob
        
        logger.info(f"Detected language {top_lang} with confidence {top_prob} using {method}")
        return top_lang, top_prob
    
    def _clean_text_for_detection(self, text: str) -> str:
        """
        Clean text for better language detection.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+\.\S+', '', text)
        
        # Remove numbers
        text = re.sub(r'\d+', '', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Take a sample if text is too long
        max_length = 1000
        if len(text) > max_length:
            # Take beginning, middle, and end
            third = max_length // 3
            text = text[:third] + " " + text[len(text)//2-third//2:len(text)//2+third//2] + " " + text[-third:]
        
        return text