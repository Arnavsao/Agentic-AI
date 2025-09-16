import os
import uuid
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from loguru import logger
import numpy as np
from config import settings
from src.data_processor import ProcessedDocument


class VectorStore:
    
    def __init__(self, collection_name: str = "gail_documents", model_name: str = "all-MiniLM-L6-v2"):
        self.collection_name = collection_name
        self.model_name = model_name
        
        logger.info(f"Loading embedding model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "GAIL website documents for RAG system"}
            )
            logger.info(f"Created new collection: {collection_name}")
        
        logger.info("VectorStore initialized successfully")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        logger.debug(f"Generating embeddings for {len(texts)} texts")
        
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.embedding_model.encode(batch, convert_to_tensor=False)
            all_embeddings.extend(embeddings.tolist())
        
        logger.debug(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings
    
    def add_documents(self, documents: List[ProcessedDocument]) -> bool:
        if not documents:
            logger.warning("No documents to add")
            return False
        
        logger.info(f"Adding {len(documents)} documents to vector store")
        
        try:
            ids = [doc.id for doc in documents]
            texts = [doc.content for doc in documents]
            metadatas = []
            
            for doc in documents:
                metadata = {
                    'title': doc.title,
                    'url': doc.url,
                    'chunk_index': doc.chunk_index,
                    'total_chunks': doc.total_chunks,
                    'page_type': doc.metadata.get('page_type', 'general'),
                    'word_count': doc.metadata.get('word_count', 0),
                    'scraped_at': doc.metadata.get('scraped_at', 0),
                    'domain': doc.metadata.get('domain', 'gailonline.com')
                }
                metadatas.append(metadata)
            
            embeddings = self.generate_embeddings(texts)
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            return False
    
    def search(
        self, 
        query: str, 
        n_results: int = 5, 
        filter_metadata: Optional[Dict] = None,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        logger.debug(f"Searching for: '{query}' (n_results={n_results})")
        
        try:
            query_embedding = self.embedding_model.encode([query], convert_to_tensor=False)[0]
            
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=filter_metadata
            )
            
            search_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    similarity_score = max(0, 1 - distance)
                    
                    if similarity_score >= score_threshold:
                        result = {
                            'content': doc,
                            'metadata': metadata,
                            'similarity_score': similarity_score,
                            'rank': i + 1
                        }
                        search_results.append(result)
            
            logger.debug(f"Found {len(search_results)} relevant results")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        try:
            results = self.collection.get(ids=[doc_id])
            
            if results['documents'] and results['documents'][0]:
                return {
                    'id': doc_id,
                    'content': results['documents'][0],
                    'metadata': results['metadatas'][0] if results['metadatas'] else {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {str(e)}")
            return None
    
    def get_collection_stats(self) -> Dict[str, Any]:
        try:
            count = self.collection.count()
            
            sample_results = self.collection.get(limit=100)
            
            page_types = {}
            total_words = 0
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    page_type = metadata.get('page_type', 'unknown')
                    page_types[page_type] = page_types.get(page_type, 0) + 1
                    total_words += metadata.get('word_count', 0)
            
            stats = {
                'total_documents': count,
                'page_types': page_types,
                'sample_word_count': total_words,
                'collection_name': self.collection_name,
                'embedding_model': self.model_name
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {'error': str(e)}
    
    def delete_documents(self, doc_ids: List[str]) -> bool:
        try:
            self.collection.delete(ids=doc_ids)
            logger.info(f"Deleted {len(doc_ids)} documents from vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            return False
    
    def reset_collection(self) -> bool:
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "GAIL website documents for RAG system"}
            )
            logger.info(f"Reset collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            return False
    
    def update_document(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        try:
            embedding = self.generate_embeddings([content])[0]
            
            self.collection.update(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
            
            logger.info(f"Updated document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {str(e)}")
            return False


def main():
    import sys
    from src.data_processor import DataProcessor
    
    if len(sys.argv) < 2:
        print("Usage: python vector_store.py <processed_data_file>")
        sys.exit(1)
    
    processed_file = sys.argv[1]
    
    processor = DataProcessor()
    processed_docs = processor.load_processed_data(processed_file)
    
    if not processed_docs:
        print("No processed documents found")
        sys.exit(1)
    
    vector_store = VectorStore()
    
    success = vector_store.add_documents(processed_docs)
    
    if success:
        stats = vector_store.get_collection_stats()
        print(f"Vector store setup complete:")
        print(f"- Total documents: {stats.get('total_documents', 0)}")
        print(f"- Page types: {stats.get('page_types', {})}")
        
        test_query = "renewable energy"
        results = vector_store.search(test_query, n_results=3)
        print(f"\nTest search for '{test_query}':")
        for result in results:
            print(f"- Score: {result['similarity_score']:.3f}")
            print(f"  Title: {result['metadata'].get('title', 'No title')}")
            print(f"  Content preview: {result['content'][:100]}...")
            print()
    else:
        print("Failed to add documents to vector store")


if __name__ == "__main__":
    main()
