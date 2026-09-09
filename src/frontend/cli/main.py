from typing import List

from torch.cuda import is_available
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.storage import RedisStore
from langchain_classic.storage._lc_store import create_kv_docstore
from langchain_classic.retrievers import MultiVectorRetriever

from utils.env import EnvConfig
from utils.db import init_qdrant_vector_store

# 1. Initialize Components (Match your ETL config)
env_config = EnvConfig()

client = QdrantClient(url=env_config.QDRANT_URL)
embedding = HuggingFaceEmbeddings(
    model_name=env_config.EMBEDDING_MODEL,
    model_kwargs={"device": "cuda" if is_available()
                  else "cpu"},
    encode_kwargs={"prompt": "passage: ", "normalize_embeddings": True},
    query_encode_kwargs={"prompt": "query: ", "normalize_embeddings": True}
)

vector_store = init_qdrant_vector_store(
    client,
    env_config.EMBEDDING_MODEL,
    env_config.QDRANT_COLLECTION_NAME,
    env_config.EMBEDDING_DIM,
    env_config.SPARSE_VECTOR_NAME
)

bytestore = RedisStore(redis_url=env_config.REDIS_URL)
docstore = create_kv_docstore(bytestore)

retriever = MultiVectorRetriever(
    vectorstore=vector_store,
    docstore=docstore,
    id_key="parent_id",
    search_kwargs={"k": 3}  # Retrieve top 3 children -> maps to top 3 parents
)

# 2. Simple CLI Loop
print("🔍 Retrieval Test CLI Started. Type 'quit' to exit.\n")
print(
    "Format: <query> | [Optional: doc_type=text/table] | [Optional: section=...]")
print("Example: How does the A-PID controller work? | doc_type=text")

while True:
    user_input = input("\n👤 Query: ").strip()
    if user_input.lower() in ['quit', 'exit', 'q']:
        break

    if not user_input:
        continue

    # Parse simple filters from input (e.g., "query | doc_type=table")
    parts = user_input.split('|')
    query = parts[0].strip()

    # Build Qdrant filter dynamically based on user input
    from qdrant_client import models
    must_conditions: List[models.Condition] = [
        models.FieldCondition(
            key="metadata.arxiv_id", match=models.MatchValue(value="2407.10173v1"))
    ]

    for part in parts[1:]:
        part = part.strip()
        if part.startswith("doc_type="):
            must_conditions.append(models.FieldCondition(
                key="metadata.doc_type", match=models.MatchValue(value=part.split("=")[1])))
        elif part.startswith("section="):
            must_conditions.append(models.FieldCondition(
                key="metadata.section", match=models.MatchValue(value=part.split("=")[1])))

    qdrant_filter = models.Filter(must=must_conditions)

    # 3. Execute Retrieval
    print(f"\n🔎 Searching for: '{query}' with filter: {qdrant_filter}")
    print("-" * 80)

    try:
        if qdrant_filter:
            child_results = vector_store.similarity_search(
                query, filter=qdrant_filter, k=3)

            # FIX 1: Safely extract parent_ids, filtering out None and ensuring type is str
            parent_ids: list[str] = []
            for doc in child_results:
                pid = doc.metadata.get("parent_id")
                if pid is not None:
                    parent_ids.append(str(pid))

            # Remove duplicates
            parent_ids = list(set(parent_ids))

            # mget returns list[Document | None], so we assign to a temporary variable
            raw_docs = docstore.mget(parent_ids)

            # FIX 2 & 3: Filter out None values that mget returns if a key is missing
            docs = [doc for doc in raw_docs if doc is not None]
        else:
            # retriever.invoke returns list[Document], which is already safe
            docs = retriever.invoke(query)

        if not docs:
            print("❌ No documents found.")
            continue

        for i, doc in enumerate(docs):
            print(f"\n📄 [Result {i+1}]")
            print(f"Metadata: {doc.metadata}")
            print(f"Content Length: {len(doc.page_content)} characters")
            # Show first 500 chars
            print(f"Content Preview:\n{doc.page_content[:2000]}...")
            print("-" * 80)

    except Exception as e:
        print(f"❌ Error during retrieval: {e}")

print("\n👋 Retrieval test ended.")
