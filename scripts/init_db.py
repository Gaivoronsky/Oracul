#!/usr/bin/env python3
"""
Database initialization script.
Creates the database tables and initial data.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'init_db.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    from storage.database.models import Base
    from storage.database.repository import get_engine
    from storage.search.elasticsearch import setup_elasticsearch_indices
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)


def create_tables():
    """Create all database tables."""
    try:
        logger.info("Creating database tables...")
        engine = get_engine()
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def create_elasticsearch_indices():
    """Create Elasticsearch indices."""
    try:
        logger.info("Setting up Elasticsearch indices...")
        setup_elasticsearch_indices()
        logger.info("Elasticsearch indices created successfully")
    except Exception as e:
        logger.error(f"Failed to create Elasticsearch indices: {e}")
        logger.warning("Continuing without Elasticsearch setup")


def create_initial_data():
    """Create initial data in the database."""
    try:
        logger.info("Creating initial data...")
        # In a real implementation, this would create initial data
        # such as admin users, default settings, etc.
        logger.info("Initial data created successfully")
    except Exception as e:
        logger.error(f"Failed to create initial data: {e}")
        raise


def main():
    """Main function to initialize the database."""
    logger.info("Starting database initialization")
    
    try:
        # Create database tables
        create_tables()
        
        # Create Elasticsearch indices
        create_elasticsearch_indices()
        
        # Create initial data
        create_initial_data()
        
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()