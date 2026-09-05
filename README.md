# Arxiv Codegen Agent

An intelligent agent system that extracts, processes, and generates code from arXiv research papers using advanced RAG (Retrieval-Augmented Generation) techniques.

## 🌟 Features

### Core Capabilities

- **Automated Paper Processing**: Fetches and processes arXiv papers automatically
- **Advanced PDF Parsing**: Uses Docling for high-quality PDF to Markdown conversion with table and code preservation
- **Hybrid Vector Search**: Combines dense and sparse embeddings in Qdrant for superior retrieval accuracy
- **Table & Code Extraction**: Preserves tables, algorithms, and code snippets from research papers
- **Intelligent Chunking**: Header-aware chunking with metadata enrichment for context-aware retrieval
- **Code Generation Agent**: LangGraph-based agent system for generating implementation code from research papers

##  Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Qdrant vector database (runs via Docker Compose)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd arxiv-reproducer-agent
```

### 2. Set Up Environment

```bash
# Copy environment example
cp .env.example .env

# Edit .env with your configuration
# Required variables:
# - QDRANT_URL (default: http://localhost:6333)
# - Any API keys if needed
```

### 3. Start Services with Docker

```bash
# Start Qdrant and other services
docker-compose up -d
```

### 4. Install Python Dependencies

```bash
# Install using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

## 📖 Usage

### Run the ETL Pipeline

Process arXiv papers and load them into Qdrant:

```bash
# Process specific papers
python etl/pipeline.py --paper_ids 2407.10173 1706.03762

# With custom options
python etl/pipeline.py \
  --paper_ids 2407.10173 \
  --qdrant_url http://localhost:6333 \
  --download_dir ./data/pdf \
  --markdown_dir ./data/markdown
```

### Use the Agent

The agent system is located in `src/arxiv_reproducer_agent/`: (Still under development)

<!-- ```python
from src.arxiv_reproducer_agent.graph import graph
from src.arxiv_reproducer_agent.state import AgentState

# Initialize and run the agent
result = graph.invoke({
    "query": "Generate code for the StatuScale framework",
    "arxiv_id": "2407.10173v1"
})
``` -->

### Access Qdrant Dashboard

Visit `http://localhost:6333/dashboard` to view your collections and indexed documents.

## 🏗️ Project Structure

```
arxiv-reproducer-agent/
├── src/
│   └── arxiv_reproducer_agent/
│       ├── nodes/          # LangGraph node implementations
│       ├── tools/          # Agent tools (retrieval, etc.)
│       ├── graph.py        # LangGraph workflow definition
│       └── state.py        # Agent state definitions
├── backend/                # Backend API (WIP)
├── frontend/                # Frontend application (WIP)
├── etl/
│   ├── extract/           # Paper fetching (arXiv API)
│   ├── transform/         # PDF parsing, cleaning, chunking
│   ├── load/              # Qdrant ingestion
│   ── pipeline.py        # Main ETL orchestration
├── utils/                 # Utility functions
├── data/                  # Downloaded papers and markdown
├── docker-compose.yaml    # Service orchestration
└── pyproject.toml         # Project dependencies
```

## 🔧 Configuration

### Environment Variables

| Variable             | Description                   | Default                          |
| -------------------- | ----------------------------- | -------------------------------- |
| `QDRANT_URL`         | Qdrant database URL           | `http://localhost:6333`          |
| `QDRANT_COLLECTION`  | Collection name               | `saved_papers`                   |
| `EMBEDDING_MODEL`    | Embedding model               | `intfloat/multilingual-e5-small` |
| `EMBEDDING_DIM`      | Embedding dimension           | `384`                            |
| `SPARSE_VECTOR_NAME` | Sparse vector collection name | `saved_papers_sparse_bm25`       |

### ETL Configuration

The ETL pipeline supports:
- **Batch Processing**: Process multiple papers in one run
- **Idempotency**: Skips already processed papers
- **Error Handling**: Continues processing on individual paper failures
- **Incremental Updates**: Only processes new or updated papers

<!-- ## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src
``` -->

## 📊 Performance

- **PDF Processing**: ~600-900 seconds per paper (with code enrichment)
- **Vector Dimensions**: 384 (dense) + sparse vectors
- **Chunk Size**: 500 tokens with 100 token overlap
- **Hybrid Search**: Combines dense embeddings with BM25 sparse vectors

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Docling** - Advanced PDF parsing and document conversion
- **Qdrant** - Vector database for semantic search
- **LangGraph** - Agent orchestration framework
- **arXiv** - Open-access research paper repository

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
<!-- - Review the examples in the `examples/` directory -->

---

**Built with ❤️ for reproducible research**