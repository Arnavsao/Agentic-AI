"""
Data processing module for cleaning and preparing scraped data for RAG system.
Handles text cleaning, chunking, and metadata extraction.
"""
import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger
import pandas as pd
from pathlib import Path


@dataclass
class ProcessedDocument:
    """Data class for processed documents."""
    id: str
    title: str
    content: str
    url: str
    metadata: Dict[str, Any]
    chunk_index: int = 0
    total_chunks: int = 1


class DataProcessor:
    """
    Data processor for cleaning and preparing scraped data.
    
    Features:
    - Text cleaning and normalization
    - Content chunking for optimal RAG performance
    - Metadata extraction and enrichment
    - Quality filtering
    """
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        """
        Initialize the data processor.
        
        Args:
            chunk_size: Maximum size of each text chunk
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Text cleaning patterns
        self.cleanup_patterns = [
            (r'\s+', ' '),  # Multiple whitespace to single space
            (r'\n+', '\n'),  # Multiple newlines to single newline
            (r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\'\/]', ''),  # Remove special chars
        ]
        
        # Stop words and common phrases to filter out
        self.stop_phrases = [
            'cookie policy', 'privacy policy', 'terms of service',
            'all rights reserved', 'copyright', 'follow us on',
            'social media', 'newsletter', 'subscribe'
        ]
        
        logger.info(f"DataProcessor initialized with chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Apply cleanup patterns
        cleaned = text
        for pattern, replacement in self.cleanup_patterns:
            cleaned = re.sub(pattern, replacement, cleaned)
        
        # Remove stop phrases
        for phrase in self.stop_phrases:
            cleaned = re.sub(re.escape(phrase), '', cleaned, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def extract_metadata(self, page_data: Dict) -> Dict[str, Any]:
        """
        Extract and enrich metadata from page data.
        
        Args:
            page_data: Raw page data from scraper
            
        Returns:
            Enriched metadata dictionary
        """
        metadata = {
            'url': page_data.get('url', ''),
            'title': page_data.get('title', ''),
            'description': page_data.get('description', ''),
            'scraped_at': page_data.get('scraped_at', 0),
            'word_count': page_data.get('word_count', 0),
            'has_images': len(page_data.get('images', [])) > 0,
            'image_count': len(page_data.get('images', [])),
            'heading_count': len(page_data.get('headings', [])),
            'domain': 'gailonline.com'
        }
        
        # Extract page type from URL
        url = page_data.get('url', '')
        if '/news/' in url:
            metadata['page_type'] = 'news'
        elif '/career/' in url or '/jobs/' in url:
            metadata['page_type'] = 'career'
        elif '/about/' in url:
            metadata['page_type'] = 'about'
        elif '/contact/' in url:
            metadata['page_type'] = 'contact'
        elif '/investor/' in url:
            metadata['page_type'] = 'investor'
        else:
            metadata['page_type'] = 'general'
        
        # Extract headings for better context
        headings = page_data.get('headings', [])
        metadata['main_headings'] = [h['text'] for h in headings if h['level'] in ['h1', 'h2']]
        
        return metadata
    
    def chunk_text(self, text: str, title: str = "") -> List[str]:
        """
        Split text into overlapping chunks for better RAG performance.
        
        Args:
            text: Text to chunk
            title: Document title for context
            
        Returns:
            List of text chunks
        """
        if not text or len(text) <= self.chunk_size:
            return [text] if text else []
        
        chunks = []
        words = text.split()
        
        # Add title to first chunk if available
        title_prefix = f"{title}\n\n" if title else ""
        
        start = 0
        while start < len(words):
            # Calculate end position
            end = min(start + self.chunk_size, len(words))
            
            # Create chunk
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            
            # Add title to first chunk
            if start == 0 and title_prefix:
                chunk_text = title_prefix + chunk_text
            
            chunks.append(chunk_text)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(words):
                break
        
        return chunks
    
    def is_quality_content(self, page_data: Dict) -> bool:
        """
        Check if page content meets quality standards.
        
        Args:
            page_data: Page data to evaluate
            
        Returns:
            True if content meets quality standards
        """
        content = page_data.get('content', '')
        word_count = page_data.get('word_count', 0)
        
        # Minimum word count
        if word_count < 50:
            return False
        
        # Check for meaningful content
        if len(content.strip()) < 100:
            return False
        
        # Check for too many repeated characters (likely corrupted)
        if any(char * 10 in content for char in [' ', '\n', '\t']):
            return False
        
        # Check for meaningful sentences
        sentences = content.split('.')
        meaningful_sentences = [s for s in sentences if len(s.strip()) > 10]
        
        if len(meaningful_sentences) < 2:
            return False
        
        return True
    
    def process_page(self, page_data: Dict) -> List[ProcessedDocument]:
        """
        Process a single page into document chunks.
        
        Args:
            page_data: Raw page data from scraper
            
        Returns:
            List of processed document chunks
        """
        if not self.is_quality_content(page_data):
            logger.warning(f"Skipping low-quality content: {page_data.get('url', 'unknown')}")
            return []
        
        # Clean content
        cleaned_content = self.clean_text(page_data.get('content', ''))
        if not cleaned_content:
            return []
        
        # Extract metadata
        metadata = self.extract_metadata(page_data)
        
        # Chunk the content
        chunks = self.chunk_text(cleaned_content, page_data.get('title', ''))
        
        # Create processed documents
        processed_docs = []
        for i, chunk in enumerate(chunks):
            doc_id = f"{page_data.get('url', 'unknown')}_chunk_{i}"
            
            doc = ProcessedDocument(
                id=doc_id,
                title=page_data.get('title', ''),
                content=chunk,
                url=page_data.get('url', ''),
                metadata=metadata,
                chunk_index=i,
                total_chunks=len(chunks)
            )
            
            processed_docs.append(doc)
        
        logger.info(f"Processed {page_data.get('url', 'unknown')} into {len(processed_docs)} chunks")
        return processed_docs
    
    def process_all_pages(self, scraped_data: List[Dict]) -> List[ProcessedDocument]:
        """
        Process all scraped pages into document chunks.
        
        Args:
            scraped_data: List of raw page data from scraper
            
        Returns:
            List of all processed document chunks
        """
        logger.info(f"Processing {len(scraped_data)} pages")
        
        all_processed_docs = []
        processed_count = 0
        skipped_count = 0
        
        for page_data in scraped_data:
            try:
                processed_docs = self.process_page(page_data)
                if processed_docs:
                    all_processed_docs.extend(processed_docs)
                    processed_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                logger.error(f"Error processing page {page_data.get('url', 'unknown')}: {str(e)}")
                skipped_count += 1
        
        logger.info(f"Processing complete:")
        logger.info(f"- Pages processed: {processed_count}")
        logger.info(f"- Pages skipped: {skipped_count}")
        logger.info(f"- Total document chunks: {len(all_processed_docs)}")
        
        return all_processed_docs
    
    def save_processed_data(self, processed_docs: List[ProcessedDocument], filename: str = "processed_documents.json"):
        """
        Save processed documents to JSON file.
        
        Args:
            processed_docs: List of processed documents
            filename: Output filename
        """
        # Convert to dictionary format for JSON serialization
        data_to_save = []
        for doc in processed_docs:
            data_to_save.append({
                'id': doc.id,
                'title': doc.title,
                'content': doc.content,
                'url': doc.url,
                'metadata': doc.metadata,
                'chunk_index': doc.chunk_index,
                'total_chunks': doc.total_chunks
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Processed data saved to {filename}")
    
    def load_processed_data(self, filename: str = "processed_documents.json") -> List[ProcessedDocument]:
        """
        Load processed documents from JSON file.
        
        Args:
            filename: Input filename
            
        Returns:
            List of processed documents
        """
        if not Path(filename).exists():
            logger.warning(f"File {filename} not found")
            return []
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        processed_docs = []
        for item in data:
            doc = ProcessedDocument(
                id=item['id'],
                title=item['title'],
                content=item['content'],
                url=item['url'],
                metadata=item['metadata'],
                chunk_index=item['chunk_index'],
                total_chunks=item['total_chunks']
            )
            processed_docs.append(doc)
        
        logger.info(f"Loaded {len(processed_docs)} processed documents from {filename}")
        return processed_docs


def main():
    """Main function to process scraped data."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python data_processor.py <scraped_data_file>")
        sys.exit(1)
    
    scraped_file = sys.argv[1]
    
    # Load scraped data
    with open(scraped_file, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    # Process data
    processor = DataProcessor()
    processed_docs = processor.process_all_pages(scraped_data)
    
    # Save processed data
    processor.save_processed_data(processed_docs)
    
    print(f"Processing complete. Generated {len(processed_docs)} document chunks.")


if __name__ == "__main__":
    main()
