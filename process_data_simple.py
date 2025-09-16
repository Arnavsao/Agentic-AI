#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from src.data_processor import DataProcessor

def main():
    if len(sys.argv) < 2:
        print("Usage: python process_data_simple.py <scraped_data_file>")
        sys.exit(1)
    
    scraped_file = sys.argv[1]
    
    print("Loading scraped data...")
    with open(scraped_file, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    print(f"Loaded {len(scraped_data)} pages")
    
    batch_size = 50
    all_processed_docs = []
    
    processor = DataProcessor(chunk_size=500, chunk_overlap=100)
    
    for i in range(0, len(scraped_data), batch_size):
        batch = scraped_data[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(scraped_data) + batch_size - 1)//batch_size}")
        
        batch_processed = processor.process_all_pages(batch)
        all_processed_docs.extend(batch_processed)
        
        del batch_processed
        del batch
    
    print(f"Processing complete. Generated {len(all_processed_docs)} document chunks.")
    
    processor.save_processed_data(all_processed_docs, "processed_documents.json")
    print("Saved to processed_documents.json")

if __name__ == "__main__":
    main()
