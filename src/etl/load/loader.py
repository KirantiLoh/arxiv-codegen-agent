from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore, FastEmbedSparse
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, SparseIndexParams, SparseVectorParams, VectorParams
import torch

QDRANT_COLLECTION_NAME = "saved_papers"
QDRANT_URL = "http://localhost:6333"
EMBEDDING_DIM = 384
SPARSE_VECTOR_NAME = "saved_papers_sparse_bm25"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

embedding = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
    encode_kwargs={"prompt": "passage: ", "normalize_embeddings": True},
    query_encode_kwargs={"prompt": "query: ", "normalize_embeddings": True}
)

sparse_embedding = FastEmbedSparse(model_name="Qdrant/bm25")


def init_qdrant_vector_store(client: QdrantClient, collection_name: str, embedding_dim: int, sparse_vector_name: str):
    """Initializes the Qdrant collection for storing embeddings and sparse vectors."""
    if not client.collection_exists(collection_name):
        print(
            f"Creating collection '{collection_name}' with {embedding_dim} dimensions...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=embedding_dim, distance=Distance.COSINE),
            sparse_vectors_config={
                sparse_vector_name: SparseVectorParams(
                    index=SparseIndexParams(
                        full_scan_threshold=500, on_disk=False)
                )
            }
        )
    else:
        print(f"Collection '{collection_name}' active.")
    return QdrantVectorStore(
        collection_name=QDRANT_COLLECTION_NAME,
        client=client,
        embedding=embedding,
        sparse_embedding=sparse_embedding,
        sparse_vector_name=SPARSE_VECTOR_NAME,
    )


def load_to_qdrant(vector_store: QdrantVectorStore, documents: list[Document]):
    """Loads a list of Document objects into the Qdrant vector store."""
    if not documents:
        print("No documents to load into Qdrant.")
        return
    print(f"Loading {len(documents)} documents into Qdrant...")
    vector_store.add_documents(documents)
    print("Documents loaded successfully.")
