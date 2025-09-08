#!/usr/bin/env python3
"""
Create a small sample dataset for testing the RAG system
"""
import json
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python create_sample_data.py <scraped_data_file>")
        sys.exit(1)
    
    scraped_file = sys.argv[1]
    
    print("Loading scraped data...")
    with open(scraped_file, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    print(f"Loaded {len(scraped_data)} pages")
    
    # Select only high-quality pages with good content
    sample_pages = []
    for page in scraped_data:
        if (page.get('word_count', 0) > 100 and 
            page.get('word_count', 0) < 5000 and
            'gailonline.com' in page.get('url', '') and
            page.get('title', '') != 'No Title'):
            sample_pages.append(page)
            if len(sample_pages) >= 20:  # Limit to 20 pages for testing
                break
    
    print(f"Selected {len(sample_pages)} high-quality pages for sample dataset")
    
    # Save sample data
    with open('sample_scraped_data.json', 'w', encoding='utf-8') as f:
        json.dump(sample_pages, f, indent=2, ensure_ascii=False)
    
    print("Sample data saved to sample_scraped_data.json")
    
    # Create simple processed documents
    processed_docs = []
    for i, page in enumerate(sample_pages):
        doc = {
            'id': f"doc_{i}",
            'title': page.get('title', 'No Title'),
            'content': page.get('content', ''),
            'url': page.get('url', ''),
            'metadata': {
                'url': page.get('url', ''),
                'title': page.get('title', ''),
                'word_count': page.get('word_count', 0),
                'scraped_at': page.get('scraped_at', 0),
                'page_type': 'general',
                'domain': 'gailonline.com'
            },
            'chunk_index': 0,
            'total_chunks': 1
        }
        processed_docs.append(doc)
    
    # Save processed documents
    with open('processed_documents.json', 'w', encoding='utf-8') as f:
        json.dump(processed_docs, f, indent=2, ensure_ascii=False)
    
    print(f"Created {len(processed_docs)} processed documents")
    print("Sample dataset ready for testing!")

if __name__ == "__main__":
    main()
