#!/usr/bin/env python3
import asyncio
import argparse
import sys
import os
from pathlib import Path
from typing import Optional
from loguru import logger

sys.path.append(str(Path(__file__).parent / "src"))

from config import settings
from src.scraper import GAILWebScraper
from src.data_processor import DataProcessor
from src.vector_store import VectorStore
from src.rag_system import RAGSystem
from src.web_app import main as run_web_app


def setup_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB"
    )
    
    Path("logs").mkdir(exist_ok=True)


async def scrape_website() -> str:
    logger.info("Starting GAIL website scraping...")
    
    async with GAILWebScraper() as scraper:
        scraped_data = await scraper.scrape_all()
        output_file = "gail_scraped_data.json"
        scraper.save_to_file(output_file)
        
        total_words = sum(page['word_count'] for page in scraped_data)
        logger.info(f"Scraping completed:")
        logger.info(f"- Total pages: {len(scraped_data)}")
        logger.info(f"- Total words: {total_words:,}")
        logger.info(f"- Average words per page: {total_words // len(scraped_data) if scraped_data else 0}")
        
        return output_file


def process_data(scraped_file: str) -> str:
    logger.info("Processing scraped data...")
    
    processor = DataProcessor()
    
    import json
    with open(scraped_file, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    processed_docs = processor.process_all_pages(scraped_data)
    output_file = "processed_documents.json"
    processor.save_processed_data(processed_docs, output_file)
    
    logger.info(f"Data processing completed. Generated {len(processed_docs)} document chunks.")
    return output_file


def setup_vector_store(processed_file: str) -> VectorStore:
    logger.info("Setting up vector database...")
    
    processor = DataProcessor()
    processed_docs = processor.load_processed_data(processed_file)
    
    if not processed_docs:
        raise ValueError("No processed documents found")
    
    vector_store = VectorStore()
    success = vector_store.add_documents(processed_docs)
    
    if not success:
        raise RuntimeError("Failed to add documents to vector store")
    stats = vector_store.get_collection_stats()
    logger.info(f"Vector store setup complete:")
    logger.info(f"- Total documents: {stats.get('total_documents', 0)}")
    logger.info(f"- Page types: {stats.get('page_types', {})}")
    
    return vector_store


def test_rag_system(vector_store: VectorStore) -> None:
    logger.info("Testing RAG system...")
    
    rag_system = RAGSystem(vector_store)
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
    logger.info("Starting full GAIL RAG Chatbot pipeline...")
    
    try:
        scraped_file = await scrape_website()
        processed_file = process_data(scraped_file)
        vector_store = setup_vector_store(processed_file)
        test_rag_system(vector_store)
        
        logger.info("Pipeline completed successfully!")
        logger.info("Starting web application...")
        
        run_web_app()
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise


def run_web_only():
    logger.info("Starting web application only...")
    
    if not Path(settings.chroma_persist_directory).exists():
        logger.error("Vector store not found. Please run the full pipeline first.")
        sys.exit(1)
    
    run_web_app()


def main():
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
    
    setup_logging()
    
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
            logger.info("No specific option provided. Running full pipeline...")
            asyncio.run(run_full_pipeline())
            
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
