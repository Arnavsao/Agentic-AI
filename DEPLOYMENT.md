# 🚀 GAIL RAG Chatbot - Deployment Guide

This guide provides comprehensive instructions for deploying your GAIL RAG Chatbot to various platforms.

## 📋 Prerequisites

Before deploying, ensure you have:

1. **OpenAI API Key** - Required for the chatbot functionality
2. **Docker** (for containerized deployment)
3. **Git** (for version control)
4. **Platform-specific tools** (see individual deployment sections)

## 🔧 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp env.example .env

# Edit .env file and add your OpenAI API key
nano .env
```

Required environment variables:
```env
OPENAI_API_KEY=your_openai_api_key_here
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

### 2. Local Development

```bash
# Install dependencies
./run.sh setup

# Run the full pipeline
./run.sh full

# Or run just the web app (if data is already processed)
./run.sh web
```

## 🐳 Docker Deployment

### Option 1: Docker Compose (Recommended)

```bash
# Deploy with Docker Compose
./deploy.sh compose

# View logs
./deploy.sh logs

# Stop application
./deploy.sh stop
```

**Access your application at:** `http://localhost`

### Option 2: Docker Only

```bash
# Deploy with Docker
./deploy.sh docker

# View logs
docker logs gail-rag-chatbot

# Stop application
docker stop gail-rag-chatbot
```

**Access your application at:** `http://localhost:8000`

## ☁️ Cloud Deployment

### Heroku Deployment

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew install heroku/brew/heroku
   
   # Ubuntu/Debian
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Deploy**
   ```bash
   ./deploy.sh heroku
   ```

4. **Access your application**
   - URL: `https://gail-rag-chatbot.herokuapp.com`
   - Health check: `https://gail-rag-chatbot.herokuapp.com/api/health`

### AWS ECS Deployment

1. **Install AWS CLI**
   ```bash
   # macOS
   brew install awscli
   
   # Ubuntu/Debian
   sudo apt-get install awscli
   ```

2. **Configure AWS**
   ```bash
   aws configure
   ```

3. **Deploy to ECS**
   ```bash
   ./deploy.sh aws-ecs
   ```

4. **Complete ECS Setup**
   - Create ECS cluster
   - Create task definition
   - Create service
   - Configure load balancer

### Google Cloud Platform (GCP)

1. **Install Google Cloud SDK**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Ubuntu/Debian
   curl https://sdk.cloud.google.com | bash
   ```

2. **Initialize and authenticate**
   ```bash
   gcloud init
   gcloud auth login
   ```

3. **Deploy to Cloud Run**
   ```bash
   # Build and push to Container Registry
   gcloud builds submit --tag gcr.io/PROJECT_ID/gail-rag-chatbot
   
   # Deploy to Cloud Run
   gcloud run deploy gail-rag-chatbot \
     --image gcr.io/PROJECT_ID/gail-rag-chatbot \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars OPENAI_API_KEY=your_key_here
   ```

### DigitalOcean App Platform

1. **Create app.yaml**
   ```yaml
   name: gail-rag-chatbot
   services:
   - name: web
     source_dir: /
     github:
       repo: your-username/gail-rag-chatbot
       branch: main
     run_command: python main.py --web-only
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
     envs:
     - key: OPENAI_API_KEY
       value: your_openai_api_key
     - key: DEBUG
       value: "false"
     - key: HOST
       value: "0.0.0.0"
     - key: PORT
       value: "8080"
   ```

2. **Deploy**
   ```bash
   doctl apps create --spec app.yaml
   ```

## 🔒 Production Considerations

### Security

1. **Environment Variables**
   - Never commit `.env` files
   - Use secure secret management
   - Rotate API keys regularly

2. **HTTPS**
   - Always use HTTPS in production
   - Configure SSL certificates
   - Use secure headers

3. **Rate Limiting**
   - Nginx configuration includes rate limiting
   - Monitor API usage
   - Implement user authentication if needed

### Performance

1. **Caching**
   - Static files are cached
   - Consider Redis for session storage
   - Implement response caching

2. **Scaling**
   - Use load balancers
   - Scale horizontally with multiple instances
   - Monitor resource usage

3. **Database**
   - ChromaDB is file-based
   - Consider external vector database for production
   - Implement backup strategies

### Monitoring

1. **Health Checks**
   - `/api/health` endpoint available
   - Docker health checks configured
   - Monitor application logs

2. **Logging**
   - Structured logging with loguru
   - Log files in `logs/` directory
   - Consider centralized logging

3. **Metrics**
   - Monitor response times
   - Track API usage
   - Set up alerts

## 🛠️ Troubleshooting

### Common Issues

1. **OpenAI API Key Not Set**
   ```bash
   # Check environment variables
   echo $OPENAI_API_KEY
   
   # Or check .env file
   cat .env | grep OPENAI_API_KEY
   ```

2. **Port Already in Use**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   
   # Kill process
   kill -9 PID
   ```

3. **Docker Build Fails**
   ```bash
   # Clean Docker cache
   docker system prune -a
   
   # Rebuild without cache
   docker build --no-cache -t gail-rag-chatbot .
   ```

4. **Vector Store Not Found**
   ```bash
   # Run full pipeline first
   ./run.sh full
   
   # Or check if chroma_db exists
   ls -la chroma_db/
   ```

### Logs and Debugging

```bash
# View application logs
./deploy.sh logs

# View Docker logs
docker logs gail-rag-chatbot

# Check container status
docker ps -a

# Enter container for debugging
docker exec -it gail-rag-chatbot /bin/bash
```

## 📊 Monitoring and Maintenance

### Health Monitoring

- **Health Check URL**: `/api/health`
- **Status Endpoint**: `/api/status`
- **System Metrics**: Available via `/api/status`

### Backup Strategy

1. **Vector Database**
   ```bash
   # Backup ChromaDB
   tar -czf chroma_db_backup.tar.gz chroma_db/
   ```

2. **Application Data**
   ```bash
   # Backup processed data
   cp processed_documents.json processed_documents_backup.json
   ```

3. **Configuration**
   ```bash
   # Backup configuration
   cp .env .env.backup
   ```

### Updates and Maintenance

1. **Update Dependencies**
   ```bash
   # Update requirements
   pip freeze > requirements.txt
   
   # Rebuild Docker image
   ./deploy.sh build
   ```

2. **Data Refresh**
   ```bash
   # Re-scrape and process data
   ./run.sh full
   ```

3. **Application Updates**
   ```bash
   # Pull latest changes
   git pull origin main
   
   # Redeploy
   ./deploy.sh compose
   ```

## 🆘 Support

If you encounter issues:

1. Check the logs: `./deploy.sh logs`
2. Verify environment variables
3. Ensure all prerequisites are installed
4. Check the troubleshooting section above

For additional help, please refer to the project documentation or create an issue in the repository.

---

**Happy Deploying! 🚀**

