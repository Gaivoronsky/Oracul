"""
Entity extractor component for the News Aggregator processor pipeline.
Extracts named entities from article content.
"""

import logging
from typing import Dict, Any, List, Optional, Set
import re
from collections import Counter

# Configure logging
logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Entity extractor component for the processing pipeline.
    Extracts named entities from article content.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the entity extractor component.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Configure extraction options
        self.enabled = self.config.get("enabled", True)
        self.min_content_length = self.config.get("min_content_length", 100)
        self.max_entities = self.config.get("max_entities", 50)
        self.min_entity_length = self.config.get("min_entity_length", 2)
        self.min_entity_occurrences = self.config.get("min_entity_occurrences", 1)
        self.entity_types = self.config.get("entity_types", ["PERSON", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "WORK_OF_ART"])
        
        # Configure models
        self.models = self.config.get("models", {
            "en": "en_core_web_sm",
            "es": "es_core_news_sm",
            "fr": "fr_core_news_sm",
            "de": "de_core_news_sm"
        })
        
        # Initialize NLP models
        self.nlp_models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """
        Initialize NLP models for entity extraction.
        """
        if not self.enabled:
            logger.info("Entity extraction is disabled")
            return
        
        try:
            import spacy
            
            # Load models for each language
            for lang, model_name in self.models.items():
                try:
                    # Check if model is installed
                    if not spacy.util.is_package(model_name):
                        logger.warning(f"Spacy model {model_name} for language {lang} is not installed")
                        continue
                    
                    # Load model
                    nlp = spacy.load(model_name, disable=["parser", "tagger"])
                    self.nlp_models[lang] = nlp
                    
                    logger.info(f"Loaded spacy model {model_name} for language {lang}")
                except Exception as e:
                    logger.error(f"Error loading spacy model {model_name} for language {lang}: {e}")
            
            if not self.nlp_models:
                logger.warning("No spacy models loaded, entity extraction will be limited")
        
        except ImportError:
            logger.warning("spacy not installed, falling back to regex-based entity extraction")
    
    async def process(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an article by extracting named entities.
        
        Args:
            article: Article data dictionary
            
        Returns:
            Processed article data dictionary
        """
        try:
            # Skip if disabled
            if not self.enabled:
                return article
            
            # Skip if no content
            if not article.get("content"):
                logger.warning(f"No content to extract entities from for article: {article.get('id', 'unknown')}")
                return article
            
            # Skip if content is too short
            if len(article["content"]) < self.min_content_length:
                logger.warning(f"Content too short for entity extraction: {len(article['content'])} chars")
                return article
            
            # Get language
            language = article.get("language", "en")
            
            # Extract entities
            entities = await self._extract_entities(article["content"], language)
            
            # Update article
            if entities:
                # Initialize entities field if not present
                if "entities" not in article:
                    article["entities"] = []
                
                # Add extracted entities
                article["entities"].extend(entities)
                
                # Remove duplicates
                article["entities"] = self._deduplicate_entities(article["entities"])
                
                # Add entity metadata
                if "metadata" not in article:
                    article["metadata"] = {}
                
                article["metadata"]["entity_count"] = len(article["entities"])
                
                # Log extraction
                logger.info(f"Extracted {len(entities)} entities from article")
            
            return article
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return article
    
    async def _extract_entities(self, text: str, language: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to extract entities from
            language: Language of the text
            
        Returns:
            List of entity dictionaries
        """
        entities = []
        
        # Use spaCy model if available for the language
        if language in self.nlp_models:
            entities = await self._extract_with_spacy(text, language)
        else:
            # Fallback to regex-based extraction
            entities = self._extract_with_regex(text, language)
        
        # Filter and limit entities
        entities = self._filter_entities(entities)
        
        return entities
    
    async def _extract_with_spacy(self, text: str, language: str) -> List[Dict[str, Any]]:
        """
        Extract entities using spaCy.
        
        Args:
            text: Text to extract entities from
            language: Language of the text
            
        Returns:
            List of entity dictionaries
        """
        entities = []
        
        try:
            nlp = self.nlp_models[language]
            
            # Process text
            doc = nlp(text)
            
            # Extract entities
            for ent in doc.ents:
                if ent.label_ in self.entity_types:
                    entity = {
                        "text": ent.text,
                        "type": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    }
                    entities.append(entity)
        
        except Exception as e:
            logger.error(f"Error extracting entities with spaCy: {e}")
        
        return entities
    
    def _extract_with_regex(self, text: str, language: str) -> List[Dict[str, Any]]:
        """
        Extract entities using regex patterns.
        
        Args:
            text: Text to extract entities from
            language: Language of the text
            
        Returns:
            List of entity dictionaries
        """
        entities = []
        
        try:
            # Simple regex patterns for common entity types
            patterns = {
                "PERSON": r'(?:[A-Z][a-z]+ ){1,2}[A-Z][a-z]+',  # Names like "John Smith"
                "ORG": r'(?:[A-Z][a-z]+ )*(?:Inc|Corp|LLC|Ltd|Company|Association|Organization)',  # Organizations
                "GPE": r'(?:[A-Z][a-z]+ )*(?:City|Town|Village|County|State|Province|Country)',  # Geo-political entities
                "LOC": r'(?:Mount|Mt\.|Lake|River|Sea|Ocean|Gulf|Bay|Peninsula|Island|Mountain) [A-Z][a-z]+',  # Locations
                "EVENT": r'(?:[A-Z][a-z]+ )*(?:Festival|Conference|Summit|Olympics|World Cup|Championship)',  # Events
            }
            
            # Extract entities using patterns
            for entity_type, pattern in patterns.items():
                if entity_type in self.entity_types:
                    matches = re.finditer(pattern, text)
                    
                    for match in matches:
                        entity = {
                            "text": match.group(),
                            "type": entity_type,
                            "start": match.start(),
                            "end": match.end()
                        }
                        entities.append(entity)
        
        except Exception as e:
            logger.error(f"Error extracting entities with regex: {e}")
        
        return entities
    
    def _filter_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter and limit entities.
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            Filtered list of entity dictionaries
        """
        # Count entity occurrences
        entity_counter = Counter([(entity["text"], entity["type"]) for entity in entities])
        
        # Filter by minimum occurrences and length
        filtered_entities = []
        for entity in entities:
            entity_key = (entity["text"], entity["type"])
            
            if (entity_counter[entity_key] >= self.min_entity_occurrences and
                    len(entity["text"]) >= self.min_entity_length):
                filtered_entities.append(entity)
        
        # Remove duplicates
        unique_entities = self._deduplicate_entities(filtered_entities)
        
        # Limit number of entities
        if self.max_entities > 0 and len(unique_entities) > self.max_entities:
            # Sort by occurrence count and take top entities
            sorted_entities = sorted(
                unique_entities,
                key=lambda e: entity_counter[(e["text"], e["type"])],
                reverse=True
            )
            unique_entities = sorted_entities[:self.max_entities]
        
        return unique_entities
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate entities.
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            Deduplicated list of entity dictionaries
        """
        # Use a set to track seen entities
        seen = set()
        unique_entities = []
        
        for entity in entities:
            # Create a key for the entity
            key = (entity["text"], entity["type"])
            
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities