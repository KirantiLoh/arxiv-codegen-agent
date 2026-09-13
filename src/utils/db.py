from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore, FastEmbedSparse, RetrievalMode
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, SparseIndexParams, SparseVectorParams, VectorParams
import torch


def init_qdrant_vector_store(client: QdrantClient, embedding_model: str, collection_name: str, embedding_dim: int, sparse_vector_name: str):
    """Initializes the Qdrant collection for storing embeddings and sparse vectors."""
    embedding = HuggingFaceEmbeddings(
        model_name=embedding_model,
        model_kwargs={"device": "cuda" if torch.cuda.is_available()
                      else "cpu"},
        encode_kwargs={"prompt": "passage: ", "normalize_embeddings": True},
        query_encode_kwargs={"prompt": "query: ", "normalize_embeddings": True}
    )

    sparse_embedding = FastEmbedSparse(model_name="Qdrant/bm25")
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
        collection_name=collection_name,
        client=client,
        embedding=embedding,
        sparse_embedding=sparse_embedding,
        sparse_vector_name=sparse_vector_name,
        retrieval_mode=RetrievalMode.HYBRID,
    )
