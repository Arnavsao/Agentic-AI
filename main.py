#!/usr/bin/env python3
"""
GAIL RAG Chatbot System - Main Entry Point
Comprehensive pipeline for scraping, processing, and serving GAIL website data.
"""
import asyncio
import argparse
import sys
import os
from pathlib import Path
from typing import Optional
from loguru import logger

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from config import settings
from src.scraper import GAILWebScraper
from src.data_processor import DataProcessor
from src.vector_store import VectorStore
from src.rag_system import RAGSystem
from src.web_app import main as run_web_app


def setup_logging():
    """Configure logging for the application."""
    logger.remove()  # Remove default handler
    
    # Add console handler with formatting
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Add file handler for errors
    logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB"
    )
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)


async def scrape_website() -> str:
    """
    Scrape GAIL website and return the output filename.
    
    Returns:
        str: Path to scraped data file
    """
    logger.info("Starting GAIL website scraping...")
    
    async with GAILWebScraper() as scraper:
        scraped_data = await scraper.scrape_all()
        output_file = "gail_scraped_data.json"
        scraper.save_to_file(output_file)
        
        # Print summary
        total_words = sum(page['word_count'] for page in scraped_data)
        logger.info(f"Scraping completed:")
        logger.info(f"- Total pages: {len(scraped_data)}")
        logger.info(f"- Total words: {total_words:,}")
        logger.info(f"- Average words per page: {total_words // len(scraped_data) if scraped_data else 0}")
        
        return output_file


def process_data(scraped_file: str) -> str:
    """
    Process scraped data and return the output filename.
    
    Args:
        scraped_file: Path to scraped data file
        
    Returns:
        str: Path to processed data file
    """
    logger.info("Processing scraped data...")
    
    processor = DataProcessor()
    
    # Load scraped data
    import json
    with open(scraped_file, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    # Process data
    processed_docs = processor.process_all_pages(scraped_data)
    
    # Save processed data
    output_file = "processed_documents.json"
    processor.save_processed_data(processed_docs, output_file)
    
    logger.info(f"Data processing completed. Generated {len(processed_docs)} document chunks.")
    return output_file


def setup_vector_store(processed_file: str) -> VectorStore:
    """
    Set up vector store with processed documents.
    
    Args:
        processed_file: Path to processed data file
        
    Returns:
        VectorStore: Initialized vector store
    """
    logger.info("Setting up vector database...")
    
    # Load processed data
    processor = DataProcessor()
    processed_docs = processor.load_processed_data(processed_file)
    
    if not processed_docs:
        raise ValueError("No processed documents found")
    
    # Initialize vector store
    vector_store = VectorStore()
    
    # Add documents
    success = vector_store.add_documents(processed_docs)
    
    if not success:
        raise RuntimeError("Failed to add documents to vector store")
    
    # Get stats
    stats = vector_store.get_collection_stats()
    logger.info(f"Vector store setup complete:")
    logger.info(f"- Total documents: {stats.get('total_documents', 0)}")
    logger.info(f"- Page types: {stats.get('page_types', {})}")
    
    return vector_store


def test_rag_system(vector_store: VectorStore) -> None:
    """
    Test the RAG system with sample queries.
    
    Args:
        vector_store: Initialized vector store
    """
    logger.info("Testing RAG system...")
    
    # Initialize RAG system
    rag_system = RAGSystem(vector_store)
    
    # Test queries
    test_queries = [
        "What is GAIL and what does it do?",
        "What are GAIL's renewable energy projects?",
        "How can I contact GAIL?"
    ]
    
    for query in test_queries:
        logger.info(f"Testing query: {query}")
        response = rag_system.process_query(query)
        logger.info(f"Response confidence: {response.confidence:.2f}")
        logger.info(f"Sources found: {len(response.sources)}")
        logger.info(f"Answer preview: {response.answer[:100]}...")
        logger.info("-" * 50)


async def run_full_pipeline():
    """Run the complete pipeline from scraping to web interface."""
    logger.info("Starting full GAIL RAG Chatbot pipeline...")
    
    try:
        # Step 1: Scrape website
        scraped_file = await scrape_website()
        
        # Step 2: Process data
        processed_file = process_data(scraped_file)
        
        # Step 3: Setup vector store
        vector_store = setup_vector_store(processed_file)
        
        # Step 4: Test RAG system
        test_rag_system(vector_store)
        
        logger.info("Pipeline completed successfully!")
        logger.info("Starting web application...")
        
        # Step 5: Start web application
        run_web_app()
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise


def run_web_only():
    """Run only the web application (assumes data is already processed)."""
    logger.info("Starting web application only...")
    
    # Check if vector store exists
    if not Path(settings.chroma_persist_directory).exists():
        logger.error("Vector store not found. Please run the full pipeline first.")
        sys.exit(1)
    
    # Start web application
    run_web_app()


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="GAIL RAG Chatbot System")
    parser.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Run the complete pipeline (scrape, process, setup, serve)"
    )
    parser.add_argument(
        "--web-only",
        action="store_true",
        help="Run only the web application (assumes data is already processed)"
    )
    parser.add_argument(
        "--scrape-only",
        action="store_true",
        help="Run only the web scraping"
    )
    parser.add_argument(
        "--process-only",
        action="store_true",
        help="Run only the data processing"
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Run only the vector store setup"
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Run only the RAG system test"
    )
    parser.add_argument(
        "--scraped-file",
        type=str,
        default="gail_scraped_data.json",
        help="Path to scraped data file (for processing)"
    )
    parser.add_argument(
        "--processed-file",
        type=str,
        default="processed_documents.json",
        help="Path to processed data file (for vector store setup)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Check for OpenAI API key
    if not settings.openai_api_key:
        logger.error("OpenAI API key not found. Please set OPENAI_API_KEY in your environment or .env file.")
        sys.exit(1)
    
    try:
        if args.full_pipeline:
            asyncio.run(run_full_pipeline())
        elif args.web_only:
            run_web_only()
        elif args.scrape_only:
            asyncio.run(scrape_website())
        elif args.process_only:
            process_data(args.scraped_file)
        elif args.setup_only:
            setup_vector_store(args.processed_file)
        elif args.test_only:
            vector_store = VectorStore()
            test_rag_system(vector_store)
        else:
            # Default: run full pipeline
            logger.info("No specific option provided. Running full pipeline...")
            asyncio.run(run_full_pipeline())
            
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
