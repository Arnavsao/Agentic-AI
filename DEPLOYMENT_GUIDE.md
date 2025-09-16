# 🚀 GAIL RAG Chatbot - Deployment Guide
## Docker, Vercel & Render

This guide covers deployment to your three chosen platforms: **Docker**, **Vercel**, and **Render**.

## 📋 Prerequisites

Before deploying, ensure you have:

1. **OpenAI API Key** - Required for the chatbot functionality
2. **Git** - For version control
3. **Platform-specific tools** (see individual sections below)

## 🔧 Quick Setup

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

### 2. Install Dependencies

```bash
# Run the installation script
python install.py

# Or manually install
pip install -r requirements.txt
```

## 🐳 Docker Deployment

### Option 1: Docker Compose (Recommended)

**Time:** 5-10 minutes

```bash
# Deploy with Docker Compose
./deploy-platforms.sh deploy compose

# View logs
./deploy-platforms.sh logs compose

# Stop deployment
./deploy-platforms.sh stop compose
```

**Access your application at:** `http://localhost`

### Option 2: Docker Only

**Time:** 5-8 minutes

```bash
# Deploy with Docker
./deploy-platforms.sh deploy docker

# View logs
./deploy-platforms.sh logs docker

# Stop deployment
./deploy-platforms.sh stop docker
```

**Access your application at:** `http://localhost:8000`

### Docker Features:
- ✅ Nginx reverse proxy with rate limiting
- ✅ Automatic SSL termination
- ✅ Health checks and monitoring
- ✅ Persistent data storage
- ✅ Easy scaling

## ⚡ Vercel Deployment

**Time:** 10-15 minutes

### Prerequisites:
```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login
```

### Deploy:
```bash
# Deploy to Vercel
./deploy-platforms.sh deploy vercel

# Or manually
vercel --prod
```

### Vercel Features:
- ✅ Serverless functions
- ✅ Automatic HTTPS
- ✅ Global CDN
- ✅ Zero configuration
- ✅ Automatic deployments from Git

### Vercel Configuration:
- **Build Command:** `pip install -r requirements.txt`
- **Output Directory:** `api/`
- **Install Command:** `pip install -r requirements.txt`

## 🌐 Render Deployment

**Time:** 15-20 minutes

### Prerequisites:
1. **GitHub Repository** - Push your code to GitHub
2. **Render Account** - Sign up at [render.com](https://render.com)

### Deploy:

#### Option 1: Using Render CLI
```bash
# Install Render CLI
curl -fsSL https://cli.render.com/install | sh

# Deploy
./deploy-platforms.sh deploy render
```

#### Option 2: Manual Deployment
1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Use these settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py --web-only`
   - **Environment:** Python 3
5. Add environment variables from your `.env` file
6. Click "Create Web Service"

### Render Features:
- ✅ Persistent disk storage
- ✅ Automatic HTTPS
- ✅ Auto-deploy from Git
- ✅ Built-in monitoring
- ✅ Easy scaling

## 📊 Platform Comparison

| Feature | Docker | Vercel | Render |
|---------|--------|--------|--------|
| **Setup Time** | 5-10 min | 10-15 min | 15-20 min |
| **Cost** | Free (local) | Free tier | Free tier |
| **Scalability** | Manual | Automatic | Automatic |
| **Persistence** | ✅ | ❌ | ✅ |
| **Custom Domain** | ✅ | ✅ | ✅ |
| **SSL** | Manual | Automatic | Automatic |
| **Git Integration** | Manual | Automatic | Automatic |

## 🎯 Recommended Deployment Path

### For Development & Testing:
```bash
# Use Docker Compose for local development
./deploy-platforms.sh deploy compose
```

### For Production:
- **Vercel** - If you need serverless and don't need persistent storage
- **Render** - If you need persistent storage and easy scaling
- **Docker** - If you want full control and custom infrastructure

## 🔍 Monitoring & Maintenance

### Check Deployment Status:
```bash
# Show status of all deployments
./deploy-platforms.sh status
```

### View Logs:
```bash
# Docker logs
./deploy-platforms.sh logs docker

# Docker Compose logs
./deploy-platforms.sh logs compose
```

### Stop Deployments:
```bash
# Stop specific deployment
./deploy-platforms.sh stop docker
./deploy-platforms.sh stop compose

# Stop all local deployments
./deploy-platforms.sh stop all
```

## 🛠️ Troubleshooting

### Common Issues:

1. **OpenAI API Key Not Set**
   ```bash
   # Check environment variables
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

4. **Vercel Deployment Fails**
   ```bash
   # Check Vercel status
   vercel ls
   
   # View deployment logs
   vercel logs
   ```

5. **Render Deployment Fails**
   - Check Render dashboard for error logs
   - Verify environment variables are set
   - Ensure build command is correct

### Health Checks:

- **Docker:** `http://localhost:8000/api/health`
- **Docker Compose:** `http://localhost/api/health`
- **Vercel:** `https://your-app.vercel.app/api/health`
- **Render:** `https://your-app.onrender.com/api/health`

## 🚀 Quick Start Commands

### Deploy Everything:
```bash
# 1. Set up environment
cp env.example .env
# Edit .env with your OpenAI API key

# 2. Deploy with Docker Compose (recommended)
./deploy-platforms.sh deploy compose

# 3. Access your app
open http://localhost
```

### Deploy to Cloud:
```bash
# Vercel (serverless)
./deploy-platforms.sh deploy vercel

# Render (with persistence)
./deploy-platforms.sh deploy render
```

## 📈 Scaling Considerations

### Docker:
- Use Docker Swarm or Kubernetes for production
- Set up load balancer
- Configure persistent volumes

### Vercel:
- Automatic scaling
- Consider upgrading plan for higher limits
- Use Vercel Edge Functions for better performance

### Render:
- Upgrade to paid plan for better performance
- Use multiple instances for high availability
- Configure custom domains

## 🆘 Support

If you encounter issues:

1. Check the logs: `./deploy-platforms.sh logs [platform]`
2. Verify environment variables
3. Ensure all prerequisites are installed
4. Check the troubleshooting section above

---

**Happy Deploying! 🚀**

Choose your platform and get your GAIL RAG Chatbot running in minutes!
