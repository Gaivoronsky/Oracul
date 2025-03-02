"""
Classifier component for the News Aggregator processor pipeline.
Classifies articles into categories.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional, Tuple
import re
from collections import Counter

# Configure logging
logger = logging.getLogger(__name__)


class Classifier:
    """
    Classifier component for the processing pipeline.
    Classifies articles into categories.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the classifier component.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Configure classification options
        self.enabled = self.config.get("enabled", True)
        self.min_content_length = self.config.get("min_content_length", 100)
        self.model_path = self.config.get("model_path", "models/classifier")
        self.categories = self.config.get("categories", [
            "politics", "business", "technology", "science", 
            "health", "sports", "entertainment"
        ])
        self.default_category = self.config.get("default_category", "general")
        self.min_confidence = self.config.get("min_confidence", 0.5)
        self.use_title = self.config.get("use_title", True)
        self.use_content = self.config.get("use_content", True)
        self.use_entities = self.config.get("use_entities", True)
        self.use_tfidf = self.config.get("use_tfidf", True)
        self.use_neural = self.config.get("use_neural", False)
        
        # Initialize models
        self.tfidf_model = None
        self.tfidf_vectorizer = None
        self.neural_model = None
        self.category_keywords = {}
        
        # Load models
        self._initialize_models()
    
    def _initialize_models(self):
        """
        Initialize classification models.
        """
        if not self.enabled:
            logger.info("Classification is disabled")
            return
        
        # Load category keywords
        self._load_category_keywords()
        
        # Initialize TF-IDF model
        if self.use_tfidf:
            self._initialize_tfidf()
        
        # Initialize neural model
        if self.use_neural:
            self._initialize_neural()
    
    def _load_category_keywords(self):
        """
        Load category keywords from file.
        """
        try:
            keywords_path = os.path.join(self.model_path, "category_keywords.json")
            
            if os.path.exists(keywords_path):
                with open(keywords_path, "r") as f:
                    self.category_keywords = json.load(f)
                
                logger.info(f"Loaded category keywords from {keywords_path}")
            else:
                logger.warning(f"Category keywords file not found: {keywords_path}")
                self._initialize_default_keywords()
        except Exception as e:
            logger.error(f"Error loading category keywords: {e}")
            self._initialize_default_keywords()
    
    def _initialize_default_keywords(self):
        """
        Initialize default category keywords.
        """
        self.category_keywords = {
            "politics": [
                "government", "president", "election", "vote", "congress", "senate",
                "parliament", "minister", "policy", "political", "democrat", "republican",
                "law", "legislation", "campaign", "candidate", "party", "bill", "vote"
            ],
            "business": [
                "company", "market", "stock", "economy", "economic", "finance", "financial",
                "investment", "investor", "profit", "revenue", "CEO", "corporation", "trade",
                "industry", "startup", "entrepreneur", "business", "commercial", "retail"
            ],
            "technology": [
                "technology", "tech", "software", "hardware", "app", "application", "computer",
                "digital", "internet", "web", "online", "device", "smartphone", "mobile",
                "innovation", "startup", "AI", "artificial intelligence", "machine learning"
            ],
            "science": [
                "science", "scientific", "research", "study", "discovery", "experiment",
                "researcher", "laboratory", "physics", "chemistry", "biology", "astronomy",
                "space", "planet", "star", "galaxy", "universe", "theory", "hypothesis"
            ],
            "health": [
                "health", "medical", "medicine", "doctor", "hospital", "patient", "disease",
                "treatment", "therapy", "drug", "vaccine", "virus", "pandemic", "epidemic",
                "symptom", "diagnosis", "healthcare", "wellness", "diet", "fitness"
            ],
            "sports": [
                "sports", "game", "player", "team", "coach", "championship", "tournament",
                "match", "competition", "win", "lose", "score", "football", "soccer",
                "basketball", "baseball", "tennis", "golf", "olympic", "athlete"
            ],
            "entertainment": [
                "entertainment", "movie", "film", "actor", "actress", "director", "music",
                "song", "album", "artist", "celebrity", "star", "TV", "television", "show",
                "series", "concert", "festival", "award", "performance", "theater"
            ]
        }
        
        logger.info("Initialized default category keywords")
    
    def _initialize_tfidf(self):
        """
        Initialize TF-IDF model.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            import joblib
            
            # Check if model files exist
            vectorizer_path = os.path.join(self.model_path, "tfidf_vectorizer.joblib")
            model_path = os.path.join(self.model_path, "tfidf_model.joblib")
            
            if os.path.exists(vectorizer_path) and os.path.exists(model_path):
                # Load model
                self.tfidf_vectorizer = joblib.load(vectorizer_path)
                self.tfidf_model = joblib.load(model_path)
                
                logger.info(f"Loaded TF-IDF model from {model_path}")
            else:
                logger.warning(f"TF-IDF model files not found: {model_path}")
                
                # Initialize empty model
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=10000,
                    stop_words="english",
                    ngram_range=(1, 2)
                )
                self.tfidf_model = LogisticRegression(
                    C=1.0,
                    class_weight="balanced",
                    max_iter=1000,
                    multi_class="ovr"
                )
        
        except ImportError:
            logger.warning("scikit-learn not installed, TF-IDF classification disabled")
            self.use_tfidf = False
        
        except Exception as e:
            logger.error(f"Error initializing TF-IDF model: {e}")
            self.use_tfidf = False
    
    def _initialize_neural(self):
        """
        Initialize neural model.
        """
        try:
            import torch
            import transformers
            
            # Check if model files exist
            model_path = os.path.join(self.model_path, "neural")
            
            if os.path.exists(model_path):
                # Load model
                self.neural_model = transformers.AutoModelForSequenceClassification.from_pretrained(model_path)
                self.neural_tokenizer = transformers.AutoTokenizer.from_pretrained(model_path)
                
                logger.info(f"Loaded neural model from {model_path}")
            else:
                logger.warning(f"Neural model files not found: {model_path}")
                
                # Initialize with pre-trained model
                model_name = "distilbert-base-uncased"
                self.neural_tokenizer = transformers.AutoTokenizer.from_pretrained(model_name)
                self.neural_model = transformers.AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    num_labels=len(self.categories)
                )
        
        except ImportError:
            logger.warning("torch or transformers not installed, neural classification disabled")
            self.use_neural = False
        
        except Exception as e:
            logger.error(f"Error initializing neural model: {e}")
            self.use_neural = False
    
    async def process(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an article by classifying it into categories.
        
        Args:
            article: Article data dictionary
            
        Returns:
            Processed article data dictionary
        """
        try:
            # Skip if disabled
            if not self.enabled:
                return article
            
            # Skip if already classified
            if article.get("categories") and not self.config.get("override_existing", False):
                logger.info(f"Article already classified: {article.get('categories')}")
                return article
            
            # Skip if no content
            if not article.get("content") and not article.get("title"):
                logger.warning(f"No content or title to classify for article: {article.get('id', 'unknown')}")
                article["categories"] = [self.default_category]
                return article
            
            # Skip if content is too short
            if article.get("content") and len(article["content"]) < self.min_content_length and not article.get("title"):
                logger.warning(f"Content too short for classification: {len(article['content'])} chars")
                article["categories"] = [self.default_category]
                return article
            
            # Classify article
            categories, confidence = await self._classify_article(article)
            
            # Update article
            if categories:
                article["categories"] = categories
                
                # Add classification metadata
                if "metadata" not in article:
                    article["metadata"] = {}
                
                article["metadata"]["classification_confidence"] = confidence
                
                # Log classification
                logger.info(f"Classified article as {categories} with confidence {confidence}")
            else:
                article["categories"] = [self.default_category]
                logger.info(f"Could not classify article, using default category: {self.default_category}")
            
            return article
        except Exception as e:
            logger.error(f"Error classifying article: {e}")
            article["categories"] = [self.default_category]
            return article
    
    async def _classify_article(self, article: Dict[str, Any]) -> Tuple[List[str], float]:
        """
        Classify an article into categories.
        
        Args:
            article: Article data dictionary
            
        Returns:
            Tuple of (list of categories, confidence)
        """
        results = []
        
        # Prepare text for classification
        text = self._prepare_text(article)
        
        # Classify with keywords
        keyword_categories, keyword_confidence = self._classify_with_keywords(text, article)
        if keyword_categories:
            results.append((keyword_categories, keyword_confidence, "keywords"))
        
        # Classify with TF-IDF
        if self.use_tfidf and self.tfidf_model and self.tfidf_vectorizer:
            tfidf_categories, tfidf_confidence = self._classify_with_tfidf(text)
            if tfidf_categories:
                results.append((tfidf_categories, tfidf_confidence, "tfidf"))
        
        # Classify with neural model
        if self.use_neural and self.neural_model and self.neural_tokenizer:
            neural_categories, neural_confidence = await self._classify_with_neural(text)
            if neural_categories:
                results.append((neural_categories, neural_confidence, "neural"))
        
        # If no results, return default category
        if not results:
            return [self.default_category], 0.0
        
        # Sort results by confidence
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Get top result
        top_categories, top_confidence, method = results[0]
        
        # If confidence is too low, use default category
        if top_confidence < self.min_confidence:
            logger.warning(f"Classification confidence too low: {top_confidence} < {self.min_confidence}")
            return [self.default_category], top_confidence
        
        logger.info(f"Classified as {top_categories} with confidence {top_confidence} using {method}")
        return top_categories, top_confidence
    
    def _prepare_text(self, article: Dict[str, Any]) -> str:
        """
        Prepare text for classification.
        
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
        
        # Add entities
        if self.use_entities and article.get("entities"):
            entity_texts = [entity["text"] for entity in article["entities"]]
            text_parts.extend(entity_texts)
        
        # Join text parts
        text = " ".join(text_parts)
        
        # Clean text
        text = self._clean_text(text)
        
        return text
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text for classification.
        
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
    
    def _classify_with_keywords(self, text: str, article: Dict[str, Any]) -> Tuple[List[str], float]:
        """
        Classify text using keyword matching.
        
        Args:
            text: Text to classify
            article: Article data dictionary
            
        Returns:
            Tuple of (list of categories, confidence)
        """
        # Count keyword matches for each category
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            
            for keyword in keywords:
                # Count occurrences of keyword
                count = text.count(keyword.lower())
                score += count
            
            # Normalize score by number of keywords
            if keywords:
                score = score / len(keywords)
            
            category_scores[category] = score
        
        # Check if article already has categories from metadata
        if article.get("metadata") and article["metadata"].get("categories"):
            metadata_categories = article["metadata"]["categories"]
            
            # Boost scores for metadata categories
            for category in metadata_categories:
                if category in category_scores:
                    category_scores[category] *= 1.5
        
        # Get top categories
        if not category_scores:
            return [], 0.0
        
        # Sort categories by score
        sorted_categories = sorted(
            category_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get top category
        top_category, top_score = sorted_categories[0]
        
        # If score is zero, return empty
        if top_score == 0:
            return [], 0.0
        
        # Get categories with scores close to top score
        threshold = top_score * 0.8
        top_categories = [
            category for category, score in sorted_categories
            if score >= threshold
        ]
        
        # Calculate confidence
        confidence = min(top_score, 1.0)
        
        return top_categories, confidence
    
    def _classify_with_tfidf(self, text: str) -> Tuple[List[str], float]:
        """
        Classify text using TF-IDF model.
        
        Args:
            text: Text to classify
            
        Returns:
            Tuple of (list of categories, confidence)
        """
        try:
            # Vectorize text
            X = self.tfidf_vectorizer.transform([text])
            
            # Predict probabilities
            probs = self.tfidf_model.predict_proba(X)[0]
            
            # Get top categories
            top_indices = probs.argsort()[::-1]
            top_probs = probs[top_indices]
            
            # Get category names
            categories = []
            for i in top_indices:
                if i < len(self.categories):
                    categories.append(self.categories[i])
            
            # Get top category
            top_category = categories[0] if categories else None
            top_prob = top_probs[0] if top_probs.size > 0 else 0.0
            
            # Get categories with probabilities close to top probability
            threshold = top_prob * 0.8
            top_categories = []
            
            for i, prob in enumerate(top_probs):
                if prob >= threshold and i < len(categories):
                    top_categories.append(categories[i])
            
            return top_categories, top_prob
        
        except Exception as e:
            logger.error(f"Error classifying with TF-IDF: {e}")
            return [], 0.0
    
    async def _classify_with_neural(self, text: str) -> Tuple[List[str], float]:
        """
        Classify text using neural model.
        
        Args:
            text: Text to classify
            
        Returns:
            Tuple of (list of categories, confidence)
        """
        try:
            import torch
            
            # Truncate text if too long
            max_length = 512
            if len(text.split()) > max_length:
                text = " ".join(text.split()[:max_length])
            
            # Tokenize text
            inputs = self.neural_tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=max_length
            )
            
            # Get predictions
            with torch.no_grad():
                outputs = self.neural_model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=1)[0].numpy()
            
            # Get top categories
            top_indices = probs.argsort()[::-1]
            top_probs = probs[top_indices]
            
            # Get category names
            categories = []
            for i in top_indices:
                if i < len(self.categories):
                    categories.append(self.categories[i])
            
            # Get top category
            top_category = categories[0] if categories else None
            top_prob = top_probs[0] if top_probs.size > 0 else 0.0
            
            # Get categories with probabilities close to top probability
            threshold = top_prob * 0.8
            top_categories = []
            
            for i, prob in enumerate(top_probs):
                if prob >= threshold and i < len(categories):
                    top_categories.append(categories[i])
            
            return top_categories, float(top_prob)
        
        except Exception as e:
            logger.error(f"Error classifying with neural model: {e}")
            return [], 0.0