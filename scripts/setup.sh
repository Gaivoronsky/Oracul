#!/bin/bash

# News Aggregator Setup Script
# This script sets up the environment for the News Aggregator application

set -e  # Exit immediately if a command exits with a non-zero status

# Print colored messages
print_message() {
  echo -e "\e[1;34m>> $1\e[0m"
}

print_success() {
  echo -e "\e[1;32m>> $1\e[0m"
}

print_error() {
  echo -e "\e[1;31m>> $1\e[0m"
}

# Check if Python 3.8+ is installed
check_python() {
  print_message "Checking Python version..."
  if command -v python3 &>/dev/null; then
    python_version=$(python3 --version | cut -d' ' -f2)
    python_major=$(echo $python_version | cut -d'.' -f1)
    python_minor=$(echo $python_version | cut -d'.' -f2)
    
    if [ "$python_major" -ge 3 ] && [ "$python_minor" -ge 8 ]; then
      print_success "Python $python_version is installed"
    else
      print_error "Python 3.8+ is required, found $python_version"
      exit 1
    fi
  else
    print_error "Python 3 is not installed"
    exit 1
  fi
}

# Check if Docker is installed
check_docker() {
  print_message "Checking Docker installation..."
  if command -v docker &>/dev/null; then
    docker_version=$(docker --version | cut -d' ' -f3 | tr -d ',')
    print_success "Docker $docker_version is installed"
  else
    print_error "Docker is not installed"
    exit 1
  fi
  
  print_message "Checking Docker Compose installation..."
  if command -v docker-compose &>/dev/null; then
    docker_compose_version=$(docker-compose --version | cut -d' ' -f3 | tr -d ',')
    print_success "Docker Compose $docker_compose_version is installed"
  else
    print_error "Docker Compose is not installed"
    exit 1
  fi
}

# Create virtual environment
create_venv() {
  print_message "Creating Python virtual environment..."
  if [ -d "venv" ]; then
    print_message "Virtual environment already exists, skipping"
  else
    python3 -m venv venv
    print_success "Virtual environment created"
  fi
  
  print_message "Activating virtual environment..."
  source venv/bin/activate
  print_success "Virtual environment activated"
}

# Install Python dependencies
install_dependencies() {
  print_message "Installing Python dependencies..."
  pip install --upgrade pip
  pip install -r requirements.txt
  print_success "Dependencies installed"
}

# Create .env file if it doesn't exist
create_env_file() {
  print_message "Creating .env file..."
  if [ -f ".env" ]; then
    print_message ".env file already exists, skipping"
  else
    cp .env.example .env
    print_success ".env file created from example"
  fi
}

# Create logs directory
create_logs_dir() {
  print_message "Creating logs directory..."
  mkdir -p logs
  print_success "Logs directory created"
}

# Initialize the database
init_database() {
  print_message "Initializing database..."
  python scripts/init_db.py
  print_success "Database initialized"
}

# Load initial sources
load_sources() {
  print_message "Loading initial news sources..."
  python scripts/load_sources.py
  print_success "Initial sources loaded"
}

# Main function
main() {
  print_message "Starting News Aggregator setup..."
  
  check_python
  check_docker
  create_venv
  install_dependencies
  create_env_file
  create_logs_dir
  init_database
  load_sources
  
  print_success "Setup completed successfully!"
  print_message "To start the application, run: docker-compose up"
}

# Run main function
main