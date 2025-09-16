"""
Vercel serverless function for GAIL RAG Chatbot
This file is required for Vercel deployment
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the FastAPI app
from src.web_app import app

# Export the app for Vercel
handler = app
