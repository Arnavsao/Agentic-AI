#!/bin/bash

# GAIL RAG Chatbot - Multi-Platform Deployment Script
# Supports Docker, Vercel, and Render deployments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_platform() {
    echo -e "${PURPLE}[PLATFORM]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
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

# Function to deploy with Docker
deploy_docker() {
    print_platform "Docker Deployment"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        print_error "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    print_status "Building Docker image..."
    docker build -t gail-rag-chatbot:latest .
    print_success "Docker image built successfully"
    
    print_status "Stopping existing container..."
    docker stop gail-rag-chatbot 2>/dev/null || true
    docker rm gail-rag-chatbot 2>/dev/null || true
    
    print_status "Starting new container..."
    docker run -d \
        --name gail-rag-chatbot \
        -p 8000:8000 \
        --env-file .env \
        -v $(pwd)/chroma_db:/app/chroma_db \
        -v $(pwd)/logs:/app/logs \
        --restart unless-stopped \
        gail-rag-chatbot:latest
    
    print_success "Docker deployment completed!"
    print_status "Access your application at: http://localhost:8000"
    print_status "API health check: http://localhost:8000/api/health"
}

# Function to deploy with Docker Compose
deploy_docker_compose() {
    print_platform "Docker Compose Deployment"
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Stopping existing containers..."
    docker-compose down 2>/dev/null || true
    
    print_status "Building and starting services..."
    docker-compose up --build -d
    
    print_success "Docker Compose deployment completed!"
    print_status "Access your application at: http://localhost"
    print_status "API health check: http://localhost/api/health"
}

# Function to deploy to Vercel
deploy_vercel() {
    print_platform "Vercel Deployment"
    
    # Check if Vercel CLI is installed
    if ! command -v vercel &> /dev/null; then
        print_error "Vercel CLI is not installed. Please install it first."
        print_error "Run: npm i -g vercel"
        exit 1
    fi
    
    # Check if logged in to Vercel
    if ! vercel whoami &> /dev/null; then
        print_error "Not logged in to Vercel. Please run 'vercel login' first."
        exit 1
    fi
    
    print_status "Deploying to Vercel..."
    
    # Set environment variables
    print_status "Setting environment variables..."
    vercel env add OPENAI_API_KEY production < <(grep OPENAI_API_KEY .env | cut -d '=' -f2)
    vercel env add DEBUG production < <(echo "false")
    vercel env add HOST production < <(echo "0.0.0.0")
    vercel env add PORT production < <(echo "8000")
    vercel env add CHROMA_PERSIST_DIRECTORY production < <(echo "/tmp/chroma_db")
    
    # Deploy
    vercel --prod
    
    print_success "Vercel deployment completed!"
    print_status "Your application will be available at the URL shown above"
}

# Function to deploy to Render
deploy_render() {
    print_platform "Render Deployment"
    
    # Check if Render CLI is installed
    if ! command -v render &> /dev/null; then
        print_warning "Render CLI not found. Please install it or deploy manually."
        print_warning "Visit: https://render.com/docs/cli"
        print_status "Manual deployment steps:"
        print_status "1. Go to https://render.com"
        print_status "2. Create a new Web Service"
        print_status "3. Connect your GitHub repository"
        print_status "4. Use these settings:"
        print_status "   - Build Command: pip install -r requirements.txt"
        print_status "   - Start Command: python main.py --web-only"
        print_status "   - Environment: Python 3"
        print_status "5. Add environment variables from your .env file"
        return
    fi
    
    print_status "Deploying to Render..."
    
    # Create render.yaml if it doesn't exist
    if [ ! -f "render.yaml" ]; then
        print_error "render.yaml not found. Please ensure it exists."
        exit 1
    fi
    
    # Deploy using Render CLI
    render services create --file render.yaml
    
    print_success "Render deployment completed!"
    print_status "Your application will be available at the URL shown above"
}

# Function to show deployment status
show_status() {
    print_status "Deployment Status:"
    
    # Docker status
    if docker ps | grep -q gail-rag-chatbot; then
        print_success "Docker: Running"
    else
        print_warning "Docker: Not running"
    fi
    
    # Docker Compose status
    if docker-compose ps | grep -q "Up"; then
        print_success "Docker Compose: Running"
    else
        print_warning "Docker Compose: Not running"
    fi
    
    # Vercel status
    if command -v vercel &> /dev/null && vercel ls &> /dev/null; then
        print_success "Vercel: Connected"
    else
        print_warning "Vercel: Not connected"
    fi
}

# Function to show logs
show_logs() {
    local platform=$1
    
    case $platform in
        "docker")
            print_status "Showing Docker logs..."
            docker logs -f gail-rag-chatbot
            ;;
        "compose")
            print_status "Showing Docker Compose logs..."
            docker-compose logs -f gail-chatbot
            ;;
        *)
            print_error "Invalid platform. Use: docker, compose"
            ;;
    esac
}

# Function to stop deployments
stop_deployment() {
    local platform=$1
    
    case $platform in
        "docker")
            print_status "Stopping Docker container..."
            docker stop gail-rag-chatbot 2>/dev/null || true
            docker rm gail-rag-chatbot 2>/dev/null || true
            print_success "Docker container stopped"
            ;;
        "compose")
            print_status "Stopping Docker Compose services..."
            docker-compose down
            print_success "Docker Compose services stopped"
            ;;
        "all")
            print_status "Stopping all local deployments..."
            docker stop gail-rag-chatbot 2>/dev/null || true
            docker rm gail-rag-chatbot 2>/dev/null || true
            docker-compose down 2>/dev/null || true
            print_success "All local deployments stopped"
            ;;
        *)
            print_error "Invalid platform. Use: docker, compose, all"
            ;;
    esac
}

# Function to show help
show_help() {
    echo "GAIL RAG Chatbot - Multi-Platform Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND] [PLATFORM]"
    echo ""
    echo "Commands:"
    echo "  deploy          - Deploy to specified platform"
    echo "  status          - Show deployment status"
    echo "  logs            - Show logs for local deployments"
    echo "  stop            - Stop local deployments"
    echo "  help            - Show this help message"
    echo ""
    echo "Platforms:"
    echo "  docker          - Deploy with Docker"
    echo "  compose         - Deploy with Docker Compose (recommended)"
    echo "  vercel          - Deploy to Vercel"
    echo "  render          - Deploy to Render"
    echo ""
    echo "Examples:"
    echo "  $0 deploy compose    # Deploy with Docker Compose"
    echo "  $0 deploy vercel     # Deploy to Vercel"
    echo "  $0 logs docker       # View Docker logs"
    echo "  $0 stop all          # Stop all local deployments"
}

# Main script logic
main() {
    local command=${1:-help}
    local platform=${2:-}
    
    case $command in
        "deploy")
            if [ -z "$platform" ]; then
                print_error "Please specify a platform"
                show_help
                exit 1
            fi
            
            check_prerequisites
            
            case $platform in
                "docker")
                    deploy_docker
                    ;;
                "compose")
                    deploy_docker_compose
                    ;;
                "vercel")
                    deploy_vercel
                    ;;
                "render")
                    deploy_render
                    ;;
                *)
                    print_error "Invalid platform: $platform"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        "status")
            show_status
            ;;
        "logs")
            if [ -z "$platform" ]; then
                print_error "Please specify a platform (docker, compose)"
                exit 1
            fi
            show_logs $platform
            ;;
        "stop")
            if [ -z "$platform" ]; then
                print_error "Please specify a platform (docker, compose, all)"
                exit 1
            fi
            stop_deployment $platform
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
