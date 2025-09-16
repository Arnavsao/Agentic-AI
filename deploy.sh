#!/bin/bash

# GAIL RAG Chatbot - Deployment Script
# This script handles deployment to various platforms

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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f "env.example" ]; then
            cp env.example .env
            print_warning "Please edit .env file and add your OpenAI API key"
            print_warning "Then run this script again"
            exit 1
        else
            print_error "env.example file not found"
            exit 1
        fi
    fi
    
    # Check if OpenAI API key is set
    if ! grep -q "OPENAI_API_KEY=sk-" .env; then
        print_error "OpenAI API key not set in .env file"
        print_error "Please add your OpenAI API key to the .env file"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image..."
    docker build -t gail-rag-chatbot:latest .
    print_success "Docker image built successfully"
}

# Function to run with Docker Compose
deploy_docker_compose() {
    print_status "Deploying with Docker Compose..."
    
    # Stop existing containers
    docker-compose down 2>/dev/null || true
    
    # Build and start services
    docker-compose up --build -d
    
    print_success "Application deployed with Docker Compose"
    print_status "Access your application at: http://localhost"
    print_status "API health check: http://localhost/api/health"
}

# Function to run with Docker only
deploy_docker() {
    print_status "Deploying with Docker..."
    
    # Stop existing container
    docker stop gail-rag-chatbot 2>/dev/null || true
    docker rm gail-rag-chatbot 2>/dev/null || true
    
    # Run container
    docker run -d \
        --name gail-rag-chatbot \
        -p 8000:8000 \
        --env-file .env \
        -v $(pwd)/chroma_db:/app/chroma_db \
        -v $(pwd)/logs:/app/logs \
        --restart unless-stopped \
        gail-rag-chatbot:latest
    
    print_success "Application deployed with Docker"
    print_status "Access your application at: http://localhost:8000"
    print_status "API health check: http://localhost:8000/api/health"
}

# Function to deploy to Heroku
deploy_heroku() {
    print_status "Deploying to Heroku..."
    
    # Check if Heroku CLI is installed
    if ! command -v heroku &> /dev/null; then
        print_error "Heroku CLI is not installed. Please install it first."
        print_error "Visit: https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    
    # Check if logged in to Heroku
    if ! heroku auth:whoami &> /dev/null; then
        print_error "Not logged in to Heroku. Please run 'heroku login' first."
        exit 1
    fi
    
    # Create Heroku app if it doesn't exist
    if ! heroku apps:info gail-rag-chatbot &> /dev/null; then
        print_status "Creating Heroku app..."
        heroku create gail-rag-chatbot
    fi
    
    # Set environment variables
    print_status "Setting environment variables..."
    heroku config:set OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d '=' -f2)
    heroku config:set DEBUG=false
    heroku config:set HOST=0.0.0.0
    heroku config:set PORT=8000
    
    # Deploy
    print_status "Deploying to Heroku..."
    git add .
    git commit -m "Deploy to Heroku" || true
    git push heroku main
    
    print_success "Application deployed to Heroku"
    print_status "Access your application at: https://gail-rag-chatbot.herokuapp.com"
}

# Function to deploy to AWS ECS
deploy_aws_ecs() {
    print_status "Deploying to AWS ECS..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if logged in to AWS
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "Not logged in to AWS. Please run 'aws configure' first."
        exit 1
    fi
    
    print_status "Building and pushing to ECR..."
    
    # Get AWS account ID and region
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=$(aws configure get region)
    
    # Create ECR repository if it doesn't exist
    aws ecr describe-repositories --repository-names gail-rag-chatbot 2>/dev/null || \
    aws ecr create-repository --repository-name gail-rag-chatbot
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
    
    # Build and push image
    docker build -t gail-rag-chatbot .
    docker tag gail-rag-chatbot:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/gail-rag-chatbot:latest
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/gail-rag-chatbot:latest
    
    print_success "Image pushed to ECR"
    print_warning "Please complete ECS task definition and service setup manually"
    print_status "ECR Image URI: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/gail-rag-chatbot:latest"
}

# Function to show logs
show_logs() {
    print_status "Showing application logs..."
    docker-compose logs -f gail-chatbot
}

# Function to stop application
stop_app() {
    print_status "Stopping application..."
    docker-compose down
    print_success "Application stopped"
}

# Function to show status
show_status() {
    print_status "Application status:"
    docker-compose ps
}

# Function to show help
show_help() {
    echo "GAIL RAG Chatbot - Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  docker          - Deploy with Docker only"
    echo "  compose         - Deploy with Docker Compose (recommended)"
    echo "  heroku          - Deploy to Heroku"
    echo "  aws-ecs         - Deploy to AWS ECS"
    echo "  build           - Build Docker image only"
    echo "  logs            - Show application logs"
    echo "  stop            - Stop application"
    echo "  status          - Show application status"
    echo "  help            - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 compose      # Deploy with Docker Compose"
    echo "  $0 heroku       # Deploy to Heroku"
    echo "  $0 logs         # View logs"
}

# Main script logic
main() {
    case "${1:-help}" in
        "docker")
            check_prerequisites
            build_image
            deploy_docker
            ;;
        "compose")
            check_prerequisites
            build_image
            deploy_docker_compose
            ;;
        "heroku")
            check_prerequisites
            deploy_heroku
            ;;
        "aws-ecs")
            check_prerequisites
            build_image
            deploy_aws_ecs
            ;;
        "build")
            check_prerequisites
            build_image
            ;;
        "logs")
            show_logs
            ;;
        "stop")
            stop_app
            ;;
        "status")
            show_status
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"

