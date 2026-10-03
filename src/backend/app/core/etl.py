import os
import uuid
import logging
import asyncio
from typing import Optional
from qdrant_client import QdrantClient
from langchain_community.storage import RedisStore
from langchain_classic.storage._lc_store import create_kv_docstore

from etl.extract.extractor import get_arxiv_paper_by_ids, download_arxiv_papers_pdf
from etl.transform.transform import convert_doc2md, clean_docling_output, init_converter, chunk_markdown_file, MarkdownHeaderTextSplitter
from utils.env import EnvConfig

logger = logging.getLogger(__name__)

async def ingest_arxiv_paper(
    arxiv_id: str,
    qdrant_client: QdrantClient,
    redis_client: RedisStore, # Note: We'll pass the redis URL to RedisStore
    download_dir: str = "./data/pdf",
    markdown_dir: str = "./data/markdown"
) -> str:
    """
    Async wrapper for the ArXiv ETL pipeline.
    Runs blocking I/O (arxiv API, docling) in a thread pool to avoid blocking FastAPI.
    """
    logger.info(f"Starting ETL ingestion for {arxiv_id}")

    # Ensure directories exist
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(markdown_dir, exist_ok=True)

    try:
        # 1. Fetch metadata (Run in thread pool)
        papers, metadata_map = await asyncio.to_thread(
            get_arxiv_paper_by_ids, [arxiv_id], None # Pass arxiv.Client() if required by your func
        )
        
        if not papers:
            raise ValueError(f"No papers found for ID: {arxiv_id}")

        paper = papers[0]
        title = paper.title
        logger.info(f"Processing: {title} ({arxiv_id})")

        # 2. Download PDF (Run in thread pool)
        await asyncio.to_thread(download_arxiv_papers_pdf, papers, download_dir)

        # 3. Convert to Markdown (Run in thread pool)
        markdown_path = f"{markdown_dir}/{arxiv_id}.md"
        if os.path.exists(markdown_path):
            logger.info(f"Markdown already exists for {arxiv_id}. Skipping conversion.")
            with open(markdown_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()
        else:
            converter = await asyncio.to_thread(init_converter)
            markdown_content = await asyncio.to_thread(
                convert_doc2md, arxiv_id, converter, input_dir=download_dir
            )
            markdown_content = await asyncio.to_thread(clean_docling_output, markdown_content)
            
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

        # 4. Initialize Retriever Components
        # Note: We use the global clients passed from main.py
        settings = EnvConfig()
        
        # Re-use or initialize vectorstore (assuming main.py handles the global one, 
        # we just need the retriever setup here)
        from utils.db import init_qdrant_vector_store
        vectorstore = init_qdrant_vector_store(
            qdrant_client, 
            settings.EMBEDDING_MODEL, 
            settings.QDRANT_COLLECTION_NAME, 
            settings.EMBEDDING_DIM, 
            f"{settings.QDRANT_COLLECTION_NAME}_sparse_bm25"
        )

        # Redis Docstore
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        bytestore = RedisStore(redis_url=redis_url, namespace="doc")
        docstore = create_kv_docstore(bytestore)

        # 5. Chunk and Store
        parent_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("##", "section"), ("###", "subsection")]
        )
        
        # Run splitting in thread pool if it's heavy, otherwise async is fine
        parent_docs = await asyncio.to_thread(parent_splitter.split_text, markdown_content)

        for doc in parent_docs:
            parent_id = str(uuid.uuid4())
            doc.metadata["parent_id"] = parent_id
            doc.metadata["arxiv_id"] = arxiv_id
            doc.metadata["title"] = title

            # Save parent to docstore
            await asyncio.to_thread(docstore.mset, [(parent_id, doc)])

            # Chunk children
            children = await asyncio.to_thread(
                chunk_markdown_file,
                markdown_content=doc.page_content,
                additional_metadata={**doc.metadata, **metadata_map.get(arxiv_id, {})},
                parent_id=parent_id
            )

            # Add children to vector store
            if children:
                vectorstore.aadd_documents(children)

        logger.info(f"ETL Pipeline completed successfully for {arxiv_id}")
        return project_id

    except Exception as e:
        logger.error(f"Failed to process {arxiv_id}: {e}", exc_info=True)
        raise
