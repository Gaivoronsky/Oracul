# News Aggregator

A comprehensive news aggregation system that collects, processes, and serves news articles from various sources.

## Features

- **Multi-source Crawling**: Collect news from RSS feeds, HTML pages, and APIs
- **Intelligent Processing**: Clean, deduplicate, and enrich news content
- **Advanced Search**: Full-text search with filtering and faceting
- **RESTful API**: Access news data programmatically
- **Modern Web Interface**: User-friendly news browsing experience
- **Analytics Dashboard**: Track news trends and statistics

## Architecture

The system consists of four main components:

1. **Crawler**: Collects news from various sources
2. **Processor**: Cleans, analyzes, and enriches news content
3. **Storage**: Stores news data in a database and search index
4. **API**: Provides access to news data via RESTful endpoints
5. **Web Interface**: Allows users to browse and search news

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- Elasticsearch
- Node.js 16+
- Docker and Docker Compose (optional)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/news-aggregator.git
   cd news-aggregator
   ```

2. Set up the environment:
   ```bash
   make setup
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Start the services:
   ```bash
   # Using Docker (recommended)
   ./docker-start.sh
   
   # Or using Docker Compose directly
   docker-compose -f docker/docker-compose.yml up -d
   
   # Or start each service individually
   make run-api
   make run-crawler
   make run-processor
   make run-web
   ```

5. Access the web interface at http://localhost:3000

### Running with Docker

The easiest way to run the entire system is using Docker:

1. Make sure Docker and Docker Compose are installed on your system
2. Clone the repository and navigate to the project directory
3. Make the startup script executable:
   ```bash
   chmod +x docker-start.sh
   ```
4. Run the startup script:
   ```bash
   ./docker-start.sh
   ```

The script will:
- Check for Docker and Docker Compose installation
- Create a `.env` file from `.env.example` if it doesn't exist
- Build and start all containers
- Initialize the database and load initial sources
- Display URLs for accessing the services

To stop all services:
```bash
docker-compose -f docker/docker-compose.yml down
```

To view logs:
```bash
docker-compose -f docker/docker-compose.yml logs -f
```

### Development

- Run tests:
  ```bash
  make test
  ```

- Lint and format code:
  ```bash
  make lint
  make format
  ```

- Create database migrations:
  ```bash
  make migrate-create message="Add new table"
  ```

- Apply database migrations:
  ```bash
  make migrate
  ```

## Project Structure

```
news-aggregator/
│
├── docker/                     # Docker configuration
│   ├── docker-compose.yml      # Service composition
│   ├── Dockerfile.api          # API service Dockerfile
│   ├── Dockerfile.crawler      # Crawler Dockerfile
│   ├── Dockerfile.processor    # Processor Dockerfile
│   └── Dockerfile.web          # Web interface Dockerfile
│
├── crawler/                    # Data collection module
│   ├── main.py                 # Entry point
│   ├── scheduler.py            # Job scheduler
│   ├── sources/                # Source adapters
│   ├── extractors/             # Content extractors
│   └── settings/               # Crawler settings
│
├── processor/                  # Data processing module
│   ├── main.py                 # Entry point
│   ├── pipeline/               # Processing pipeline
│   ├── deduplication/          # Deduplication logic
│   └── utils/                  # Utilities
│
├── storage/                    # Data storage module
│   ├── database/               # Database operations
│   ├── search/                 # Search index operations
│   └── migrations/             # Database migrations
│
├── api/                        # API module
│   ├── main.py                 # Entry point
│   ├── routes/                 # API routes
│   ├── middlewares/            # Middleware components
│   └── services/               # Business logic
│
├── web/                        # Web interface
│   ├── public/                 # Static files
│   ├── src/                    # React source code
│   ├── package.json            # NPM dependencies
│   └── webpack.config.js       # Build configuration
│
├── scripts/                    # Utility scripts
├── tests/                      # Tests
├── logs/                       # Log files
│
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── Makefile                    # Project commands
├── README.md                   # This file
└── setup.py                    # Installation script
```

## API Documentation

The API documentation is available at http://localhost:8000/docs when the API service is running.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.