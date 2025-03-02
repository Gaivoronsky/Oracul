"""
Elasticsearch integration for the News Aggregator application.
Provides functionality for indexing and searching news articles.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import NotFoundError, ConnectionError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Elasticsearch configuration
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ES_USERNAME = os.getenv("ELASTICSEARCH_USERNAME", "elastic")
ES_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD", "changeme")
ES_INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX_NAME", "news_articles")
ES_TIMEOUT = int(os.getenv("ELASTICSEARCH_TIMEOUT", "30"))


def get_elasticsearch_client() -> Elasticsearch:
    """
    Create and return an Elasticsearch client.
    """
    try:
        es = Elasticsearch(
            [ES_URL],
            basic_auth=(ES_USERNAME, ES_PASSWORD),
            timeout=ES_TIMEOUT
        )
        # Check connection
        if not es.ping():
            logger.warning("Could not connect to Elasticsearch")
            return None
        return es
    except ConnectionError as e:
        logger.error(f"Failed to connect to Elasticsearch: {e}")
        return None


def setup_elasticsearch_indices():
    """
    Set up Elasticsearch indices with proper mappings.
    """
    es = get_elasticsearch_client()
    if not es:
        logger.error("Elasticsearch client not available")
        return False

    # Define index mapping
    mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "text", "analyzer": "standard"},
                "content": {"type": "text", "analyzer": "standard"},
                "summary": {"type": "text", "analyzer": "standard"},
                "published_at": {"type": "date"},
                "author": {"type": "keyword"},
                "source_id": {"type": "integer"},
                "source_name": {"type": "keyword"},
                "url": {"type": "keyword"},
                "image_url": {"type": "keyword"},
                "language": {"type": "keyword"},
                "sentiment_score": {"type": "float"},
                "categories": {"type": "keyword"},
                "entities": {
                    "properties": {
                        "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "type": {"type": "keyword"}
                    }
                },
                "tags": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "standard": {
                        "type": "standard",
                        "stopwords": "_english_"
                    }
                }
            }
        }
    }

    try:
        # Check if index exists
        if es.indices.exists(index=ES_INDEX_NAME):
            logger.info(f"Index {ES_INDEX_NAME} already exists")
            return True

        # Create index with mapping
        es.indices.create(index=ES_INDEX_NAME, body=mapping)
        logger.info(f"Created index {ES_INDEX_NAME} with mapping")
        return True
    except Exception as e:
        logger.error(f"Failed to create Elasticsearch index: {e}")
        return False


def index_article(article_data: Dict[str, Any]) -> bool:
    """
    Index a single article in Elasticsearch.
    
    Args:
        article_data: Dictionary containing article data
        
    Returns:
        bool: True if indexing was successful, False otherwise
    """
    es = get_elasticsearch_client()
    if not es:
        logger.error("Elasticsearch client not available")
        return False

    try:
        # Prepare document
        doc_id = article_data.get("id")
        if not doc_id:
            logger.error("Article ID is required for indexing")
            return False

        # Index document
        es.index(index=ES_INDEX_NAME, id=doc_id, document=article_data)
        logger.info(f"Indexed article with ID {doc_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to index article: {e}")
        return False


def bulk_index_articles(articles_data: List[Dict[str, Any]]) -> bool:
    """
    Bulk index multiple articles in Elasticsearch.
    
    Args:
        articles_data: List of dictionaries containing article data
        
    Returns:
        bool: True if bulk indexing was successful, False otherwise
    """
    es = get_elasticsearch_client()
    if not es:
        logger.error("Elasticsearch client not available")
        return False

    try:
        # Prepare bulk actions
        actions = [
            {
                "_index": ES_INDEX_NAME,
                "_id": article.get("id"),
                "_source": article
            }
            for article in articles_data
            if article.get("id")
        ]

        if not actions:
            logger.warning("No valid articles to index")
            return False

        # Bulk index
        success, failed = helpers.bulk(es, actions, stats_only=True)
        logger.info(f"Bulk indexed {success} articles, {failed} failed")
        return failed == 0
    except Exception as e:
        logger.error(f"Failed to bulk index articles: {e}")
        return False


def delete_article(article_id: int) -> bool:
    """
    Delete an article from the Elasticsearch index.
    
    Args:
        article_id: ID of the article to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    es = get_elasticsearch_client()
    if not es:
        logger.error("Elasticsearch client not available")
        return False

    try:
        es.delete(index=ES_INDEX_NAME, id=article_id)
        logger.info(f"Deleted article with ID {article_id} from index")
        return True
    except NotFoundError:
        logger.warning(f"Article with ID {article_id} not found in index")
        return False
    except Exception as e:
        logger.error(f"Failed to delete article from index: {e}")
        return False


def search_articles(
    query: str,
    categories: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    entities: Optional[List[str]] = None,
    date_from: Optional[Union[str, datetime]] = None,
    date_to: Optional[Union[str, datetime]] = None,
    language: Optional[str] = None,
    sort_by: str = "relevance",
    page: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Search for articles in Elasticsearch.
    
    Args:
        query: Search query
        categories: List of categories to filter by
        sources: List of sources to filter by
        entities: List of entities to filter by
        date_from: Start date for filtering
        date_to: End date for filtering
        language: Language to filter by
        sort_by: Field to sort by (relevance, date, sentiment)
        page: Page number
        limit: Number of results per page
        
    Returns:
        Dictionary containing search results and metadata
    """
    es = get_elasticsearch_client()
    if not es:
        logger.error("Elasticsearch client not available")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "pages": 0,
            "query": query
        }

    try:
        # Calculate offset
        offset = (page - 1) * limit

        # Build query
        must_conditions = []
        filter_conditions = []
        
        # Full-text search
        if query:
            must_conditions.append({
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "summary^2", "content"],
                    "type": "best_fields"
                }
            })
        
        # Category filter
        if categories:
            filter_conditions.append({
                "terms": {"categories": categories}
            })
        
        # Source filter
        if sources:
            filter_conditions.append({
                "terms": {"source_name": sources}
            })
        
        # Entity filter
        if entities:
            filter_conditions.append({
                "terms": {"entities.name.keyword": entities}
            })
        
        # Date range filter
        date_range = {}
        if date_from:
            date_range["gte"] = date_from
        if date_to:
            date_range["lte"] = date_to
        if date_range:
            filter_conditions.append({
                "range": {"published_at": date_range}
            })
        
        # Language filter
        if language:
            filter_conditions.append({
                "term": {"language": language}
            })
        
        # Build the full query
        body = {
            "query": {
                "bool": {
                    "must": must_conditions,
                    "filter": filter_conditions
                }
            },
            "from": offset,
            "size": limit,
            "track_total_hits": True
        }
        
        # Add sorting
        if sort_by == "date":
            body["sort"] = [{"published_at": {"order": "desc"}}]
        elif sort_by == "sentiment":
            body["sort"] = [{"sentiment_score": {"order": "desc"}}]
        # Default is relevance, which doesn't need explicit sorting
        
        # Execute search
        response = es.search(index=ES_INDEX_NAME, body=body)
        
        # Process results
        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        
        items = [hit["_source"] for hit in hits]
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": total_pages,
            "query": query
        }
    except Exception as e:
        logger.error(f"Failed to search articles: {e}")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "pages": 0,
            "query": query
        }


def get_article_by_id(article_id: int) -> Optional[Dict[str, Any]]:
    """
    Get an article from Elasticsearch by ID.
    
    Args:
        article_id: ID of the article to retrieve
        
    Returns:
        Article data or None if not found
    """
    es = get_elasticsearch_client()
    if not es:
        logger.error("Elasticsearch client not available")
        return None

    try:
        response = es.get(index=ES_INDEX_NAME, id=article_id)
        return response["_source"]
    except NotFoundError:
        logger.warning(f"Article with ID {article_id} not found in index")
        return None
    except Exception as e:
        logger.error(f"Failed to get article from index: {e}")
        return None


def get_suggestions(query: str, field: str = "title", limit: int = 5) -> List[str]:
    """
    Get search suggestions based on a partial query.
    
    Args:
        query: Partial search query
        field: Field to get suggestions from
        limit: Maximum number of suggestions
        
    Returns:
        List of suggestions
    """
    es = get_elasticsearch_client()
    if not es:
        logger.error("Elasticsearch client not available")
        return []

    try:
        body = {
            "suggest": {
                "text": query,
                "simple_phrase": {
                    "phrase": {
                        "field": field,
                        "size": limit,
                        "gram_size": 3,
                        "direct_generator": [
                            {
                                "field": field,
                                "suggest_mode": "always"
                            }
                        ],
                        "highlight": {
                            "pre_tag": "",
                            "post_tag": ""
                        }
                    }
                }
            }
        }
        
        response = es.search(index=ES_INDEX_NAME, body=body)
        suggestions = []
        
        for suggestion in response["suggest"]["simple_phrase"]:
            for option in suggestion["options"]:
                suggestions.append(option["text"])
        
        return suggestions[:limit]
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        return []


def get_facets(
    query: str,
    categories: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    date_from: Optional[Union[str, datetime]] = None,
    date_to: Optional[Union[str, datetime]] = None,
    language: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get facets (aggregations) for search results.
    
    Args:
        query: Search query
        categories: List of categories to filter by
        sources: List of sources to filter by
        date_from: Start date for filtering
        date_to: End date for filtering
        language: Language to filter by
        
    Returns:
        Dictionary containing facets
    """
    es = get_elasticsearch_client()
    if not es:
        logger.error("Elasticsearch client not available")
        return {
            "categories": [],
            "sources": [],
            "languages": [],
            "entities": []
        }

    try:
        # Build query
        must_conditions = []
        filter_conditions = []
        
        # Full-text search
        if query:
            must_conditions.append({
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "summary^2", "content"],
                    "type": "best_fields"
                }
            })
        
        # Category filter
        if categories:
            filter_conditions.append({
                "terms": {"categories": categories}
            })
        
        # Source filter
        if sources:
            filter_conditions.append({
                "terms": {"source_name": sources}
            })
        
        # Date range filter
        date_range = {}
        if date_from:
            date_range["gte"] = date_from
        if date_to:
            date_range["lte"] = date_to
        if date_range:
            filter_conditions.append({
                "range": {"published_at": date_range}
            })
        
        # Language filter
        if language:
            filter_conditions.append({
                "term": {"language": language}
            })
        
        # Build the full query with aggregations
        body = {
            "query": {
                "bool": {
                    "must": must_conditions,
                    "filter": filter_conditions
                }
            },
            "size": 0,  # We only want aggregations, not results
            "aggs": {
                "categories": {
                    "terms": {
                        "field": "categories",
                        "size": 20
                    }
                },
                "sources": {
                    "terms": {
                        "field": "source_name",
                        "size": 20
                    }
                },
                "languages": {
                    "terms": {
                        "field": "language",
                        "size": 10
                    }
                },
                "entities": {
                    "terms": {
                        "field": "entities.name.keyword",
                        "size": 20
                    }
                }
            }
        }
        
        # Execute search
        response = es.search(index=ES_INDEX_NAME, body=body)
        
        # Process aggregations
        result = {
            "categories": [],
            "sources": [],
            "languages": [],
            "entities": []
        }
        
        for agg_name, agg_data in response["aggregations"].items():
            for bucket in agg_data["buckets"]:
                result[agg_name].append({
                    "key": bucket["key"],
                    "count": bucket["doc_count"]
                })
        
        return result
    except Exception as e:
        logger.error(f"Failed to get facets: {e}")
        return {
            "categories": [],
            "sources": [],
            "languages": [],
            "entities": []
        }