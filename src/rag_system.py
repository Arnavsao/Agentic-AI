import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
import openai
from config import settings
from src.vector_store import VectorStore


@dataclass
class RAGResponse:
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    query: str
    context_used: str


class RAGSystem:
    
    def __init__(self, vector_store: VectorStore, model_name: str = "gpt-3.5-turbo"):
        self.vector_store = vector_store
        self.model_name = model_name
        
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in environment variables.")
        
        openai.api_key = settings.openai_api_key
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        
        self.system_prompt = """You are an intelligent assistant specialized in answering questions about GAIL (Gas Authority of India Limited) based on their official website content.

Your role:
- Provide accurate, helpful answers based on the provided context from GAIL's website
- If the context doesn't contain enough information, clearly state this
- Always cite sources when providing information
- Be professional and informative in your responses
- Focus on GAIL's business, services, policies, and corporate information

Guidelines:
- Use only the provided context to answer questions
- If asked about topics not covered in the context, politely explain that you can only answer questions about GAIL based on the available information
- Structure your answers clearly with relevant details
- Include relevant statistics, dates, or specific information when available
- Maintain a helpful and professional tone

Context will be provided with each query. Use this context to provide accurate and comprehensive answers."""

        self.conversation_history: List[Dict[str, str]] = []
        
        logger.info(f"RAG System initialized with model: {model_name}")
    
    def optimize_query(self, query: str) -> str:
        gail_keywords = ["GAIL", "Gas Authority of India", "natural gas", "pipeline", "energy"]
        
        query_lower = query.lower()
        has_gail_context = any(keyword.lower() in query_lower for keyword in gail_keywords)
        
        if not has_gail_context:
            optimized_query = f"GAIL {query}"
        else:
            optimized_query = query
        
        logger.debug(f"Query optimized: '{query}' -> '{optimized_query}'")
        return optimized_query
    
    def retrieve_context(self, query: str, n_results: int = 5) -> Tuple[List[Dict], str]:
        optimized_query = self.optimize_query(query)
        search_results = self.vector_store.search(
            query=optimized_query,
            n_results=n_results,
            score_threshold=0.0  # Lower threshold for testing
        )
        
        if not search_results:
            logger.warning(f"No relevant context found for query: {query}")
            return [], ""
        
        context_parts = []
        for i, result in enumerate(search_results):
            source_info = f"Source {i+1}: {result['metadata'].get('title', 'Unknown')} (URL: {result['metadata'].get('url', 'Unknown')})"
            context_parts.append(f"{source_info}\nContent: {result['content']}\n")
        
        combined_context = "\n".join(context_parts)
        
        logger.info(f"Retrieved {len(search_results)} relevant documents for query")
        return search_results, combined_context
    
    def generate_answer(
        self, 
        query: str, 
        context: str, 
        conversation_history: Optional[List[Dict]] = None
    ) -> Tuple[str, float]:
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            
            if conversation_history:
                messages.extend(conversation_history[-6:])  # Last 6 exchanges
            
            context_message = f"""Based on the following context from GAIL's official website, please answer the user's question:

CONTEXT:
{context}

USER QUESTION: {query}

Please provide a comprehensive answer based on the context above. If the context doesn't contain enough information to answer the question, please state this clearly."""
            
            messages.append({"role": "user", "content": context_message})
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=1000,
                temperature=0.3,  # Lower temperature for more focused responses
                top_p=0.9
            )
            
            answer = response.choices[0].message.content.strip()
            
            confidence = min(0.9, len(answer) / 200)  # Simple confidence metric
            
            logger.info(f"Generated answer with confidence: {confidence:.2f}")
            return answer, confidence
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return f"I apologize, but I encountered an error while generating a response. Please try again.", 0.0
    
    def process_query(self, query: str, include_sources: bool = True) -> RAGResponse:
        logger.info(f"Processing query: {query}")
        
        search_results, context = self.retrieve_context(query)
        
        if not context:
            return RAGResponse(
                answer="I apologize, but I couldn't find relevant information about your question in GAIL's website content. Please try rephrasing your question or ask about GAIL's business, services, or policies.",
                sources=[],
                confidence=0.0,
                query=query,
                context_used=""
            )
        
        answer, confidence = self.generate_answer(query, context, self.conversation_history)
        
        sources = []
        if include_sources and search_results:
            for result in search_results:
                source = {
                    'title': result['metadata'].get('title', 'Unknown'),
                    'url': result['metadata'].get('url', ''),
                    'similarity_score': result['similarity_score'],
                    'page_type': result['metadata'].get('page_type', 'general')
                }
                sources.append(source)
        
        self.conversation_history.append({"role": "user", "content": query})
        self.conversation_history.append({"role": "assistant", "content": answer})
        
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        response = RAGResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            query=query,
            context_used=context
        )
        
        logger.info(f"Query processed successfully. Confidence: {confidence:.2f}")
        return response
    
    def get_suggested_questions(self) -> List[str]:
        stats = self.vector_store.get_collection_stats()
        page_types = stats.get('page_types', {})
        
        suggestions = [
            "What is GAIL and what does it do?",
            "What are GAIL's main business areas?",
            "How can I contact GAIL?",
            "What career opportunities are available at GAIL?",
            "What is GAIL's renewable energy portfolio?",
            "Tell me about GAIL's pipeline network",
            "What are GAIL's CSR initiatives?",
            "How does GAIL contribute to India's energy sector?"
        ]
        
        if 'news' in page_types:
            suggestions.append("What are the latest news and updates from GAIL?")
        if 'investor' in page_types:
            suggestions.append("What is GAIL's financial performance?")
        if 'career' in page_types:
            suggestions.append("What job opportunities are available at GAIL?")
        
        return suggestions[:8]
    
    def clear_conversation_history(self):
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        return self.conversation_history.copy()


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python rag_system.py <query>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    vector_store = VectorStore()
    rag_system = RAGSystem(vector_store)
    
    response = rag_system.process_query(query)
    
    print(f"Query: {response.query}")
    print(f"Answer: {response.answer}")
    print(f"Confidence: {response.confidence:.2f}")
    
    if response.sources:
        print("\nSources:")
        for i, source in enumerate(response.sources, 1):
            print(f"{i}. {source['title']} (Score: {source['similarity_score']:.3f})")
            print(f"   URL: {source['url']}")


if __name__ == "__main__":
    main()
