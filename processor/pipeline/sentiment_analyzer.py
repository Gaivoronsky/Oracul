"""
Sentiment analyzer component for the News Aggregator processor pipeline.
Analyzes the sentiment of article content.
"""

import logging
import os
import re
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Sentiment analyzer component for the processing pipeline.
    Analyzes the sentiment of article content.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the sentiment analyzer component.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Configure sentiment analysis options
        self.enabled = self.config.get("enabled", True)
        self.min_content_length = self.config.get("min_content_length", 100)
        self.model_path = self.config.get("model_path", "models/sentiment")
        self.default_language = self.config.get("default_language", "en")
        self.use_title = self.config.get("use_title", True)
        self.use_content = self.config.get("use_content", True)
        self.use_vader = self.config.get("use_vader", True)
        self.use_textblob = self.config.get("use_textblob", True)
        self.use_transformers = self.config.get("use_transformers", False)
        
        # Initialize models
        self.vader_analyzer = None
        self.textblob_analyzer = None
        self.transformers_analyzer = None
        self.transformers_tokenizer = None
        
        # Load models
        self._initialize_models()
    
    def _initialize_models(self):
        """
        Initialize sentiment analysis models.
        """
        if not self.enabled:
            logger.info("Sentiment analysis is disabled")
            return
        
        # Initialize VADER
        if self.use_vader:
            self._initialize_vader()
        
        # Initialize TextBlob
        if self.use_textblob:
            self._initialize_textblob()
        
        # Initialize Transformers
        if self.use_transformers:
            self._initialize_transformers()
    
    def _initialize_vader(self):
        """
        Initialize VADER sentiment analyzer.
        """
        try:
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            import nltk
            
            # Download VADER lexicon if not already downloaded
            try:
                nltk.data.find("vader_lexicon")
            except LookupError:
                nltk.download("vader_lexicon")
            
            # Initialize analyzer
            self.vader_analyzer = SentimentIntensityAnalyzer()
            
            logger.info("Initialized VADER sentiment analyzer")
        
        except ImportError:
            logger.warning("nltk not installed, VADER sentiment analysis disabled")
            self.use_vader = False
        
        except Exception as e:
            logger.error(f"Error initializing VADER sentiment analyzer: {e}")
            self.use_vader = False
    
    def _initialize_textblob(self):
        """
        Initialize TextBlob sentiment analyzer.
        """
        try:
            import textblob
            
            # Initialize analyzer (just import the module)
            self.textblob_analyzer = True
            
            logger.info("Initialized TextBlob sentiment analyzer")
        
        except ImportError:
            logger.warning("textblob not installed, TextBlob sentiment analysis disabled")
            self.use_textblob = False
        
        except Exception as e:
            logger.error(f"Error initializing TextBlob sentiment analyzer: {e}")
            self.use_textblob = False
    
    def _initialize_transformers(self):
        """
        Initialize Transformers sentiment analyzer.
        """
        try:
            import torch
            import transformers
            
            # Check if model files exist
            model_path = os.path.join(self.model_path, "transformers")
            
            if os.path.exists(model_path):
                # Load model
                self.transformers_analyzer = transformers.AutoModelForSequenceClassification.from_pretrained(model_path)
                self.transformers_tokenizer = transformers.AutoTokenizer.from_pretrained(model_path)
                
                logger.info(f"Loaded Transformers sentiment model from {model_path}")
            else:
                logger.warning(f"Transformers sentiment model files not found: {model_path}")
                
                # Initialize with pre-trained model
                model_name = "distilbert-base-uncased-finetuned-sst-2-english"
                self.transformers_tokenizer = transformers.AutoTokenizer.from_pretrained(model_name)
                self.transformers_analyzer = transformers.AutoModelForSequenceClassification.from_pretrained(model_name)
                
                logger.info(f"Initialized Transformers sentiment model with {model_name}")
        
        except ImportError:
            logger.warning("torch or transformers not installed, Transformers sentiment analysis disabled")
            self.use_transformers = False
        
        except Exception as e:
            logger.error(f"Error initializing Transformers sentiment analyzer: {e}")
            self.use_transformers = False
    
    async def process(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an article by analyzing its sentiment.
        
        Args:
            article: Article data dictionary
            
        Returns:
            Processed article data dictionary
        """
        try:
            # Skip if disabled
            if not self.enabled:
                return article
            
            # Skip if already analyzed
            if "sentiment" in article and not self.config.get("override_existing", False):
                logger.info(f"Article already has sentiment analysis: {article['sentiment']}")
                return article
            
            # Skip if no content
            if not article.get("content") and not article.get("title"):
                logger.warning(f"No content or title to analyze sentiment for article: {article.get('id', 'unknown')}")
                return article
            
            # Skip if content is too short
            if article.get("content") and len(article["content"]) < self.min_content_length and not article.get("title"):
                logger.warning(f"Content too short for sentiment analysis: {len(article['content'])} chars")
                return article
            
            # Get language
            language = article.get("language", self.default_language)
            
            # Analyze sentiment
            sentiment, confidence = await self._analyze_sentiment(article, language)
            
            # Update article
            article["sentiment"] = sentiment
            
            # Add sentiment metadata
            if "metadata" not in article:
                article["metadata"] = {}
            
            article["metadata"]["sentiment_confidence"] = confidence
            
            # Log analysis
            logger.info(f"Analyzed sentiment as {sentiment} with confidence {confidence}")
            
            return article
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return article
    
    async def _analyze_sentiment(self, article: Dict[str, Any], language: str) -> Tuple[str, float]:
        """
        Analyze the sentiment of an article.
        
        Args:
            article: Article data dictionary
            language: Language of the article
            
        Returns:
            Tuple of (sentiment, confidence)
        """
        results = []
        
        # Prepare text for analysis
        text = self._prepare_text(article)
        
        # Analyze with VADER
        if self.use_vader and self.vader_analyzer and language == "en":
            vader_sentiment, vader_confidence = self._analyze_with_vader(text)
            results.append((vader_sentiment, vader_confidence, "vader"))
        
        # Analyze with TextBlob
        if self.use_textblob and self.textblob_analyzer:
            textblob_sentiment, textblob_confidence = self._analyze_with_textblob(text, language)
            results.append((textblob_sentiment, textblob_confidence, "textblob"))
        
        # Analyze with Transformers
        if self.use_transformers and self.transformers_analyzer and self.transformers_tokenizer:
            transformers_sentiment, transformers_confidence = await self._analyze_with_transformers(text)
            results.append((transformers_sentiment, transformers_confidence, "transformers"))
        
        # If no results, return neutral
        if not results:
            return "neutral", 0.0
        
        # Sort results by confidence
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Get top result
        top_sentiment, top_confidence, method = results[0]
        
        logger.info(f"Analyzed sentiment as {top_sentiment} with confidence {top_confidence} using {method}")
        return top_sentiment, top_confidence
    
    def _prepare_text(self, article: Dict[str, Any]) -> str:
        """
        Prepare text for sentiment analysis.
        
        Args:
            article: Article data dictionary
            
        Returns:
            Prepared text
        """
        text_parts = []
        
        # Add title
        if self.use_title and article.get("title"):
            # Add title multiple times to give it more weight
            text_parts.extend([article["title"]] * 3)
        
        # Add content
        if self.use_content and article.get("content"):
            text_parts.append(article["content"])
        
        # Join text parts
        text = " ".join(text_parts)
        
        # Clean text
        text = self._clean_text(text)
        
        return text
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text for sentiment analysis.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+\.\S+', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _analyze_with_vader(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment using VADER.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (sentiment, confidence)
        """
        try:
            # Get sentiment scores
            scores = self.vader_analyzer.polarity_scores(text)
            
            # Determine sentiment
            compound = scores["compound"]
            
            if compound >= 0.05:
                sentiment = "positive"
            elif compound <= -0.05:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            # Calculate confidence
            confidence = abs(compound)
            
            return sentiment, confidence
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment with VADER: {e}")
            return "neutral", 0.0
    
    def _analyze_with_textblob(self, text: str, language: str) -> Tuple[str, float]:
        """
        Analyze sentiment using TextBlob.
        
        Args:
            text: Text to analyze
            language: Language of the text
            
        Returns:
            Tuple of (sentiment, confidence)
        """
        try:
            from textblob import TextBlob
            
            # Create TextBlob
            blob = TextBlob(text)
            
            # Get sentiment
            polarity = blob.sentiment.polarity
            
            # Determine sentiment
            if polarity > 0.1:
                sentiment = "positive"
            elif polarity < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            # Calculate confidence
            confidence = abs(polarity)
            
            return sentiment, confidence
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment with TextBlob: {e}")
            return "neutral", 0.0
    
    async def _analyze_with_transformers(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment using Transformers.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (sentiment, confidence)
        """
        try:
            import torch
            
            # Truncate text if too long
            max_length = 512
            if len(text.split()) > max_length:
                text = " ".join(text.split()[:max_length])
            
            # Tokenize text
            inputs = self.transformers_tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=max_length
            )
            
            # Get predictions
            with torch.no_grad():
                outputs = self.transformers_analyzer(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=1)[0].numpy()
            
            # Determine sentiment
            # Assuming binary classification: [negative, positive]
            if probs[1] > 0.6:
                sentiment = "positive"
                confidence = float(probs[1])
            elif probs[0] > 0.6:
                sentiment = "negative"
                confidence = float(probs[0])
            else:
                sentiment = "neutral"
                confidence = 1.0 - abs(float(probs[1] - 0.5) * 2)
            
            return sentiment, confidence
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment with Transformers: {e}")
            return "neutral", 0.0