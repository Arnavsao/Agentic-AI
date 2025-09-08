#!/bin/bash

# GAIL RAG Chatbot System - Run Script
# This script provides easy commands to run different parts of the system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Python version: $python_version"
}

# Function to check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
}

# Function to activate virtual environment
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_status "Virtual environment activated"
    else
        print_error "Virtual environment activation script not found"
        exit 1
    fi
}

# Function to install dependencies
install_deps() {
    print_status "Installing dependencies..."
    pip install --upgrade pip setuptools wheel
    
    # Check Python version and use appropriate requirements file
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ "$python_version" == "3.13" ]]; then
        print_status "Detected Python 3.13, using compatible requirements..."
        pip install -r requirements-py313.txt
    else
        pip install -r requirements.txt
    fi
    print_success "Dependencies installed"
}

# Function to check environment variables
check_env() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "Please edit .env file and add your OpenAI API key"
        else
            print_error ".env.example file not found"
            exit 1
        fi
    fi
    
    # Check if OpenAI API key is set
    if ! grep -q "OPENAI_API_KEY=sk-" .env; then
        print_warning "OpenAI API key not set in .env file"
        print_warning "Please add your OpenAI API key to the .env file"
    fi
}

# Function to create necessary directories
create_dirs() {
    print_status "Creating necessary directories..."
    mkdir -p logs
    mkdir -p static/css
    mkdir -p static/js
    mkdir -p templates
    mkdir -p chroma_db
    print_success "Directories created"
}

# Function to run the full pipeline
run_full_pipeline() {
    print_status "Running full GAIL RAG Chatbot pipeline..."
    python main.py --full-pipeline
}

# Function to run only the web application
run_web_only() {
    print_status "Running web application only..."
    python main.py --web-only
}

# Function to run only scraping
run_scrape_only() {
    print_status "Running web scraping only..."
    python main.py --scrape-only
}

# Function to run only data processing
run_process_only() {
    print_status "Running data processing only..."
    python main.py --process-only
}

# Function to run only vector store setup
run_setup_only() {
    print_status "Running vector store setup only..."
    python main.py --setup-only
}

# Function to test the RAG system
run_test_only() {
    print_status "Testing RAG system..."
    python main.py --test-only
}

# Function to show help
show_help() {
    echo "GAIL RAG Chatbot System - Run Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup       - Set up the environment and install dependencies"
    echo "  full        - Run the complete pipeline (scrape, process, setup, serve)"
    echo "  web         - Run only the web application"
    echo "  scrape      - Run only the web scraping"
    echo "  process     - Run only the data processing"
    echo "  setup-db    - Run only the vector store setup"
    echo "  test        - Test the RAG system"
    echo "  clean       - Clean up generated files"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup    # First time setup"
    echo "  $0 full     # Run everything"
    echo "  $0 web      # Just start the web app"
}

# Function to clean up generated files
cleanup() {
    print_status "Cleaning up generated files..."
    rm -f gail_scraped_data.json
    rm -f processed_documents.json
    rm -rf chroma_db/*
    rm -rf logs/*
    print_success "Cleanup completed"
}

# Main script logic
main() {
    case "${1:-help}" in
        "setup")
            print_status "Setting up GAIL RAG Chatbot System..."
            check_python
            check_venv
            activate_venv
            install_deps
            create_dirs
            check_env
            print_success "Setup completed! Run '$0 full' to start the pipeline."
            ;;
        "full")
            check_python
            activate_venv
            run_full_pipeline
            ;;
        "web")
            check_python
            activate_venv
            run_web_only
            ;;
        "scrape")
            check_python
            activate_venv
            run_scrape_only
            ;;
        "process")
            check_python
            activate_venv
            run_process_only
            ;;
        "setup-db")
            check_python
            activate_venv
            run_setup_only
            ;;
        "test")
            check_python
            activate_venv
            run_test_only
            ;;
        "clean")
            cleanup
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
