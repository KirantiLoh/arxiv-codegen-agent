from dotenv import load_dotenv
import os


class EnvConfig:
    """Class to hold environment variable configurations."""

    def __init__(self, env_file: str = ".env"):
        load_dotenv(dotenv_path=env_file)
        self.QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.QDRANT_COLLECTION_NAME = os.getenv(
            "QDRANT_COLLECTION_NAME", "saved_papers")
        self.EMBEDDING_MODEL = os.getenv(
            "EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
        self.SPARSE_VECTOR_NAME = os.getenv(
            "SPARSE_VECTOR_NAME", "saved_papers_sparse_bm25")
        self.EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 384))
