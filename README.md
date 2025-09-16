# GAIL RAG Chatbot System

A comprehensive Retrieval-Augmented Generation (RAG) system that scrapes data from GAIL's official website and provides intelligent question-answering capabilities through a modern web interface.

##  Features

- **Comprehensive Web Scraping**: Async scraping of GAIL's entire website with respectful crawling
- **Intelligent Data Processing**: Text cleaning, chunking, and metadata extraction
- **Vector Database**: ChromaDB integration for efficient similarity search
- **RAG System**: OpenAI GPT integration for intelligent responses
- **Modern Web Interface**: Responsive chat interface with real-time interactions
- **Source Attribution**: Transparent source citations for all responses
- **Conversation Memory**: Context-aware conversations with history management

##  Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Internet connection for web scraping

##  Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd gail-rag-chatbot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Configure settings** (optional):
   Edit `config.py` to customize scraping parameters, model settings, etc.

##  Quick Start

### Option 1: Full Pipeline (Recommended)

Run the complete pipeline from scraping to web interface:

```bash
python main.py --full-pipeline
```

This will:
1. Scrape GAIL's website
2. Process and clean the data
3. Generate embeddings and store in vector database
4. Start the web application

### Option 2: Step-by-Step

1. **Scrape GAIL's website**:
   ```bash
   python src/scraper.py
   ```

2. **Process scraped data**:
   ```bash
   python src/data_processor.py gail_scraped_data.json
   ```

3. **Set up vector database**:
   ```bash
   python src/vector_store.py processed_documents.json
   ```

4. **Start the web application**:
   ```bash
   python src/web_app.py
   ```

##  Usage

1. **Start the application**:
   ```bash
   python main.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:8000
   ```

3. **Start chatting** with the GAIL assistant!

##  Project Structure

```
gail-rag-chatbot/
├── src/
│   ├── __init__.py
│   ├── scraper.py          # Web scraping module
│   ├── data_processor.py   # Data cleaning and processing
│   ├── vector_store.py     # Vector database operations
│   ├── rag_system.py       # RAG system implementation
│   └── web_app.py          # FastAPI web application
├── templates/
│   ├── index.html          # Main chat interface
│   ├── 404.html            # Error page
│   └── 500.html            # Server error page
├── static/
│   ├── css/
│   │   └── style.css       # Custom styles
│   └── js/
│       └── chat.js         # Frontend JavaScript
├── config.py               # Configuration settings
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

##  Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Web Scraping Configuration
USER_AGENT=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
REQUEST_DELAY=1
MAX_RETRIES=3

# Application Configuration
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

### Scraping Configuration

Modify `config.py` to customize scraping behavior:

- `request_delay`: Delay between requests (seconds)
- `max_retries`: Maximum retry attempts for failed requests
- `timeout`: Request timeout (seconds)
- `chunk_size`: Text chunk size for processing
- `chunk_overlap`: Overlap between text chunks

## 🔧 API Endpoints

The web application provides the following API endpoints:

- `GET /` - Main chat interface
- `POST /api/chat` - Send chat message
- `GET /api/status` - System status and statistics
- `GET /api/suggestions` - Get suggested questions
- `POST /api/clear-history` - Clear conversation history
- `GET /api/health` - Health check

##  System Components

### 1. Web Scraper (`src/scraper.py`)

- **Async scraping** for better performance
- **Respectful crawling** with configurable delays
- **Error handling** and retry logic
- **Content deduplication**
- **Progress tracking**

### 2. Data Processor (`src/data_processor.py`)

- **Text cleaning** and normalization
- **Content chunking** for optimal RAG performance
- **Metadata extraction** and enrichment
- **Quality filtering**

### 3. Vector Store (`src/vector_store.py`)

- **ChromaDB integration** for vector storage
- **Sentence transformer** embeddings
- **Similarity search** with metadata filtering
- **Batch operations** for efficiency

### 4. RAG System (`src/rag_system.py`)

- **Context retrieval** from vector store
- **OpenAI GPT integration** for answer generation
- **Source attribution** and confidence scoring
- **Conversation memory**

### 5. Web Interface (`src/web_app.py`)

- **FastAPI backend** with async support
- **Responsive frontend** with modern UI
- **Real-time chat** interface
- **Source visualization**

##  Example Queries

Try asking the GAIL assistant:

- "What is GAIL and what does it do?"
- "What are GAIL's renewable energy projects?"
- "How can I contact GAIL for business inquiries?"
- "What career opportunities are available at GAIL?"
- "Tell me about GAIL's pipeline network"
- "What are GAIL's CSR initiatives?"

##  Monitoring and Logging

The system includes comprehensive logging using `loguru`:

- **Scraping progress** and errors
- **Data processing** statistics
- **Vector store** operations
- **RAG system** performance
- **Web application** requests

Logs are displayed in the console and can be configured for file output.

##  Troubleshooting

### Common Issues

1. **OpenAI API Key Error**:
   - Ensure your API key is correctly set in the `.env` file
   - Verify you have sufficient API credits

2. **Scraping Failures**:
   - Check internet connection
   - Verify GAIL's website is accessible
   - Adjust `request_delay` in config if getting rate limited

3. **Vector Store Issues**:
   - Ensure ChromaDB directory is writable
   - Check available disk space

4. **Web Application Won't Start**:
   - Verify all dependencies are installed
   - Check if port 8000 is available
   - Review error logs for specific issues

### Performance Optimization

- **Increase chunk size** for better context retention
- **Adjust similarity threshold** for more/less strict matching
- **Use smaller embedding models** for faster processing
- **Implement caching** for frequently asked questions

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

##  License

This project is licensed under the MIT License - see the LICENSE file for details.

##  Acknowledgments

- GAIL (India) Limited for providing the source data
- OpenAI for the GPT models
- ChromaDB for vector storage
- FastAPI for the web framework
- All open-source contributors

##  Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs for error details
3. Open an issue on GitHub
4. Contact the development team

---

**Note**: This system is designed for educational and research purposes. Please respect GAIL's website terms of service and implement appropriate rate limiting for production use.