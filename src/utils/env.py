from dotenv import load_dotenv, find_dotenv
import os


class EnvConfig:
    """Class to hold environment variable configurations."""

    def __init__(self, env_file: str = ""):
        load_dotenv(dotenv_path=env_file if env_file != "" else find_dotenv())
        self.QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.QDRANT_COLLECTION_NAME = os.getenv(
            "QDRANT_COLLECTION_NAME", "saved_papers")
        self.EMBEDDING_MODEL = os.getenv(
            "EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
        self.SPARSE_VECTOR_NAME = os.getenv(
            "SPARSE_VECTOR_NAME", "saved_papers_sparse_bm25")
        self.EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 384))
        self.LANGSMITH_TRACING = os.getenv(
            "LANGSMITH_TRACING", "false") == "true"
        self.LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
        self.REDIS_URL = os.getenv("REDIS_URL", "")
