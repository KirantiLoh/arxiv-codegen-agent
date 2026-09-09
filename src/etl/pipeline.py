
import argparse
import os
import logging
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def pipeline(paper_ids, download_dir, markdown_dir, redis_url="redis://:arxiv-codegen-pw@localhost:6379", qdrant_url="http://localhost:6333", qdrant_collection_name="saved_papers"):
    from etl.extract.extractor import get_arxiv_paper_by_ids, download_arxiv_papers_pdf
    from etl.transform.transform import convert_doc2md, clean_docling_output, init_converter, chunk_markdown_file, MarkdownHeaderTextSplitter
    from utils.db import init_qdrant_vector_store
    from qdrant_client import QdrantClient
    import uuid
    import arxiv
    from langchain_classic.retrievers import MultiVectorRetriever
    from langchain_community.storage import RedisStore
    from langchain_classic.storage._lc_store import create_kv_docstore

    from utils.env import EnvConfig

    client = QdrantClient(url=qdrant_url)
    converter = init_converter()
    papers, metadata_map = get_arxiv_paper_by_ids(paper_ids, arxiv.Client())

    if not papers:
        logging.warning("No papers found for the provided IDs.")
        return

    logging.info("Downloading PDFs...")
    download_arxiv_papers_pdf(papers, download_dir)

    logging.info("Initializing Qdrant vector store...")
    vector_store = init_qdrant_vector_store(
        client, EnvConfig(
        ).EMBEDDING_MODEL, qdrant_collection_name, 384, f"{qdrant_collection_name}_sparse_bm25"
    )

    bytestore = RedisStore(redis_url=redis_url)

    docstore = create_kv_docstore(bytestore)

    retriever = MultiVectorRetriever(
        docstore=docstore,
        id_key="parent_id",
        vectorstore=vector_store
    )

    for paper in papers:
        arxiv_id = paper.get_short_id()
        title = paper.title
        logging.info(f"Processing: {title} ({arxiv_id})")

        markdown_path = f"{markdown_dir}/{arxiv_id}.md"

        try:
            if os.path.exists(markdown_path):
                logging.info(
                    f"Markdown already exists for {arxiv_id}. Skipping conversion.")
                with open(markdown_path, "r", encoding="utf-8") as f:
                    markdown_content = f.read()
            else:
                markdown_content = convert_doc2md(
                    arxiv_id, converter, input_dir=download_dir)
                markdown_content = clean_docling_output(markdown_content)
                with open(markdown_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

            parent_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=[("##", "section")]
            )
            parent_docs = parent_splitter.split_text(markdown_content)

            for doc in parent_docs:
                parent_id = str(uuid.uuid4())
                doc.metadata["parent_id"] = parent_id

                # Save to the docstore
                retriever.docstore.mset([(parent_id, doc)])

                children = chunk_markdown_file(
                    markdown_content=doc.page_content,
                    additional_metadata={
                        **doc.metadata, **metadata_map[arxiv_id]},
                    parent_id=parent_id
                )

                retriever.vectorstore.add_documents(children)

        except Exception as e:
            logging.error(f"Failed to process {arxiv_id}: {e}")
            continue

    logging.info("ETL Pipeline completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ETL pipeline for fetching, converting, and loading arXiv papers.",
        usage="python pipeline.py [options] paper_id1 paper_id2 ...")
    parser.add_argument("--redis_url", type=str,
                        default="redis://:arxiv-codegen-pw@localhost:6379", help="URL of the Redis instance.")
    parser.add_argument("--qdrant_url", type=str,
                        default="http://localhost:6333", help="URL of the Qdrant instance.")
    parser.add_argument("--qdrant_collection_name", type=str, default="saved_papers",
                        help="Name of the Qdrant collection to store embeddings.")
    parser.add_argument("--download_dir", type=str,
                        default="./data/pdf", help="Directory to download PDFs.")
    parser.add_argument("--markdown_dir", type=str, default="./data/markdown",
                        help="Directory to save Markdown files.")
    parser.add_argument("paper_ids", nargs="+", type=str,
                        help="List of arXiv paper IDs to fetch.")
    if len(sys.argv) <= 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    start = time.perf_counter()
    pipeline(args.paper_ids, qdrant_url=args.qdrant_url,
             qdrant_collection_name=args.qdrant_collection_name, download_dir=args.download_dir, markdown_dir=args.markdown_dir)
    end = time.perf_counter()
    logging.info(
        f"Total time taken for the ETL pipeline: {end - start:.2f} seconds")
