"""
FastAPI web application for the GAIL RAG Chatbot.
Provides a modern web interface for interacting with the RAG system.
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from loguru import logger
import uvicorn

from config import settings
from src.vector_store import VectorStore
from src.rag_system import RAGSystem, RAGResponse


# Pydantic models for API
class ChatMessage(BaseModel):
    message: str
    timestamp: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    timestamp: str
    suggested_questions: List[str]


class SystemStatus(BaseModel):
    status: str
    vector_store_stats: Dict[str, Any]
    total_documents: int
    last_updated: Optional[str] = None


# Initialize FastAPI app
app = FastAPI(
    title="GAIL RAG Chatbot",
    description="Intelligent chatbot for GAIL website information",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global variables for RAG system
vector_store: Optional[VectorStore] = None
rag_system: Optional[RAGSystem] = None


def get_rag_system() -> RAGSystem:
    """Dependency to get the RAG system instance."""
    global rag_system
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    return rag_system


def get_vector_store() -> VectorStore:
    """Dependency to get the vector store instance."""
    global vector_store
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    return vector_store


@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system on startup."""
    global vector_store, rag_system
    
    try:
        logger.info("Initializing RAG system...")
        
        # Initialize vector store
        vector_store = VectorStore()
        
        # Initialize RAG system
        rag_system = RAGSystem(vector_store)
        
        logger.info("RAG system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {str(e)}")
        raise


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main chat interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    rag: RAGSystem = Depends(get_rag_system)
):
    """Handle chat messages and return responses."""
    try:
        # Process the query
        response = rag.process_query(message.message)
        
        # Get suggested questions
        suggested_questions = rag.get_suggested_questions()
        
        # Create response
        chat_response = ChatResponse(
            answer=response.answer,
            sources=response.sources,
            confidence=response.confidence,
            timestamp=datetime.now().isoformat(),
            suggested_questions=suggested_questions
        )
        
        logger.info(f"Processed chat message: {message.message[:50]}...")
        return chat_response
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/status", response_model=SystemStatus)
async def get_status(
    vector_store: VectorStore = Depends(get_vector_store)
):
    """Get system status and statistics."""
    try:
        stats = vector_store.get_collection_stats()
        
        status = SystemStatus(
            status="operational",
            vector_store_stats=stats,
            total_documents=stats.get('total_documents', 0),
            last_updated=datetime.now().isoformat()
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/suggestions")
async def get_suggestions(rag: RAGSystem = Depends(get_rag_system)):
    """Get suggested questions."""
    try:
        suggestions = rag.get_suggested_questions()
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/clear-history")
async def clear_history(rag: RAGSystem = Depends(get_rag_system)):
    """Clear conversation history."""
    try:
        rag.clear_conversation_history()
        return {"message": "Conversation history cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors."""
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)


def main():
    """Run the web application."""
    logger.info("Starting GAIL RAG Chatbot web application")
    
    uvicorn.run(
        "src.web_app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )


if __name__ == "__main__":
    main()
