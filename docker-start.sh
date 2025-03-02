#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== News Aggregator Docker Startup ===${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if .env file exists, if not create it from .env.example
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}Created .env file from .env.example. Please review and update the values if needed.${NC}"
    else
        echo -e "${RED}Error: .env.example file not found. Please create a .env file manually.${NC}"
        exit 1
    fi
fi

# Create logs directory if it doesn't exist
if [ ! -d logs ]; then
    echo -e "${YELLOW}Creating logs directory...${NC}"
    mkdir -p logs
fi

# Build and start the containers
echo -e "${GREEN}Building and starting Docker containers...${NC}"
docker-compose -f docker/docker-compose.yml up -d --build

# Check if containers are running
echo -e "${GREEN}Checking container status...${NC}"
sleep 5
CONTAINERS=$(docker-compose -f docker/docker-compose.yml ps -q)
if [ -z "$CONTAINERS" ]; then
    echo -e "${RED}Error: No containers are running. Please check the logs for errors.${NC}"
    docker-compose -f docker/docker-compose.yml logs
    exit 1
fi

# Initialize the database
echo -e "${GREEN}Initializing the database...${NC}"
docker-compose -f docker/docker-compose.yml exec api python -m scripts.init_db

# Load initial sources
echo -e "${GREEN}Loading initial news sources...${NC}"
docker-compose -f docker/docker-compose.yml exec api python -m scripts.load_sources

echo -e "${GREEN}=== News Aggregator is now running! ===${NC}"
echo -e "${GREEN}API is available at: http://localhost:8000${NC}"
echo -e "${GREEN}Web interface is available at: http://localhost:3000${NC}"
echo -e "${GREEN}To stop the services, run: docker-compose -f docker/docker-compose.yml down${NC}"