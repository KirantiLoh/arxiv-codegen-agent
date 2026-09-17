import os
import json
import time
import csv
import numpy as np
from typing import List

from qdrant_client import QdrantClient
from langchain_community.storage import RedisStore
from langchain_classic.storage._lc_store import create_kv_docstore
from langchain_classic.retrievers import MultiVectorRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from torch.cuda import is_available

from utils.db import init_qdrant_vector_store
from utils.env import EnvConfig

TOP_K = 5

# ==============================================================================
# 1. INITIALIZE LOCAL EMBEDDING MODEL (The "Relevance Judger")
# ==============================================================================
env_config = EnvConfig()
print(f"🧠 Loading local embedding model: {env_config.EMBEDDING_MODEL}...")
embeddings = HuggingFaceEmbeddings(
    model_name=env_config.EMBEDDING_MODEL,
    model_kwargs={"device": "cuda" if is_available() else "cpu"},
    # Crucial for Cosine Similarity
    encode_kwargs={"normalize_embeddings": True}
)

# Cache embeddings to speed up the evaluation
_embedding_cache = {}


def get_embedding(text: str) -> np.ndarray:
    if text not in _embedding_cache:
        _embedding_cache[text] = embeddings.embed_query(text)
    return _embedding_cache[text]


# ==============================================================================
# 2. CLASSIC IR METRICS (Powered by Semantic Similarity)
# ==============================================================================
RELEVANCE_THRESHOLD = 0.75  # If cosine similarity > 0.75, the chunk is "Relevant"


def is_relevant(expected_answer: str, chunk: str) -> bool:
    """
    Determines if a retrieved chunk contains the answer.
    Uses Embedding Cosine Similarity to perfectly handle LaTeX and Math formulas.
    """
    emb_answer = get_embedding(expected_answer)
    emb_chunk = get_embedding(chunk)
    # Dot product of normalized vectors = Cosine Similarity
    similarity = float(np.dot(emb_answer, emb_chunk))
    return similarity >= RELEVANCE_THRESHOLD


def compute_precision_at_k(expected_answer: str, chunks: List[str], k: int = 5) -> float:
    """Precision@K: What fraction of the top-K chunks are actually relevant?"""
    if not chunks:
        return 0.0
    relevant_count = sum(
        1 for chunk in chunks[:k] if is_relevant(expected_answer, chunk))
    return relevant_count / min(k, len(chunks))


def compute_recall_at_k(expected_answer: str, chunks: List[str], k: int = 5) -> float:
    """
    Fractional Recall@K: Returns the highest cosine similarity 
    between the expected answer and any chunk in the top-K,
    representing HOW WELL the best retrieved chunk covers the expected answer.
    """
    if not chunks:
        return 0.0

    emb_answer = get_embedding(expected_answer)

    # Calculate similarity with each chunk in top-K
    best_similarity = 0.0
    for chunk in chunks[:k]:
        emb_chunk = get_embedding(chunk)
        similarity = float(np.dot(emb_answer, emb_chunk))
        if similarity > best_similarity:
            best_similarity = similarity

    # Clamp between 0 and 1
    return max(0.0, min(1.0, best_similarity))


def compute_mrr(expected_answer: str, chunks: List[str]) -> float:
    """Mean Reciprocal Rank: At what position did the first relevant chunk appear?"""
    for i, chunk in enumerate(chunks):
        if is_relevant(expected_answer, chunk):
            return 1.0 / (i + 1)
    return 0.0


# ==============================================================================
# 3. LOAD DATA & RETRIEVER
# ==============================================================================
with open("eval/retrieval/golden_testcases_2407.10173v1.json", "r", encoding="utf-8") as f:
    test_cases_data = json.load(f)

client = QdrantClient(url=env_config.QDRANT_URL)
vectorstore = init_qdrant_vector_store(
    client, env_config.EMBEDDING_MODEL, env_config.QDRANT_COLLECTION_NAME,
    env_config.EMBEDDING_DIM, env_config.SPARSE_VECTOR_NAME,
)
bytestore = RedisStore(redis_url=env_config.REDIS_URL, namespace="doc")
docstore = create_kv_docstore(bytestore)

retriever = MultiVectorRetriever(
    docstore=docstore, id_key="parent_id", vectorstore=vectorstore,
    search_kwargs={"k": 5}
)

# ==============================================================================
# 4. RUN EVALUATION
# ==============================================================================
print(f"\n🚀 Running Classic IR Metrics (Powered by Semantic Embeddings)...")
print(
    f"   Relevance Threshold: {RELEVANCE_THRESHOLD}\n")

results = []
latency_results = []
failed_tests = []

for i, data in enumerate(test_cases_data):
    start_time = time.perf_counter()
    docs = retriever.invoke(data["question"])
    end_time = time.perf_counter()

    latency_ms = (end_time - start_time) * 1000
    latency_results.append(latency_ms)

    retrieved_contexts = [doc.page_content for doc in docs]
    expected_answer = data["expected_answer"]

    # Compute the Classic Metrics using the Semantic Judger
    p_at_k = compute_precision_at_k(expected_answer, retrieved_contexts, k=5)
    r_at_k = compute_recall_at_k(expected_answer, retrieved_contexts, k=5)
    mrr = compute_mrr(expected_answer, retrieved_contexts)

    results.append({
        "id": data.get("id", i + 1),
        "category": data.get("category", "unknown"),
        "question": data["question"],
        "expected_answer": data["expected_answer"],
        "Token_Overlap": round(mrr, 4),
        f"Precision@{TOP_K}": round(p_at_k, 4),
        f"Recall@{TOP_K}": round(r_at_k, 4),
        "MRR": round(mrr, 4),
        "Latency_ms": round(latency_ms, 2),
        "Chunks_Retrieved": len(docs),
        "retrieved_docs": docs,
    })
    status = "✅"
    if r_at_k < RELEVANCE_THRESHOLD:
        status = "❌"
        failed_tests.append(i)
    print(f"  {status} Test {i+1:2d}/{len(test_cases_data)} | "
          f"P@{TOP_K}: {p_at_k:.2f} | "
          f"R@{TOP_K}: {r_at_k:.2f} | "
          f"MRR: {mrr:.2f} | "
          f"{latency_ms:.0f}ms | "
          f"[{data.get('category', '?')}]")

# ==============================================================================
# 5. SAVE & PRINT SUMMARY
# ==============================================================================
output_dir = "eval/retrieval"
os.makedirs(output_dir, exist_ok=True)
csv_path = f"{output_dir}/final_classical_ir_results.csv"

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

avg_p = sum(r[f"Precision@{TOP_K}"] for r in results) / len(results)
avg_r = sum(r[f"Recall@{TOP_K}"] for r in results) / len(results)
avg_mrr = sum(r["MRR"] for r in results) / len(results)
avg_latency = sum(latency_results) / len(latency_results)

print("\n" + "=" * 70)
print("📊 FINAL CLASSICAL IR EVALUATION RESULTS")
print("=" * 70)
print(f"  📈 Average Precision@{TOP_K}:  {avg_p:.4f}")
print(f"  📈 Average Recall@{TOP_K}:     {avg_r:.4f}")
print(f"  📈 Average MRR:          {avg_mrr:.4f}")
print(f"  ⏱️  Average Latency:      {avg_latency:.2f} ms")
if len(failed_tests) > 0:
    print("=" * 70)
    print("🔍 DEBUGGING: Inspecting Retrieved Chunks for Failing Math Tests")
    print("="*70)

    for data in test_cases_data:
        if data.get("id") in failed_tests:
            docs = retriever.invoke(data["question"])

            print(f"\n❌ TEST {data['id']}: {data['question'][:60]}...")
            print(f"Expected Answer: {data['expected_answer'][:50]}...")

            for i, doc in enumerate(docs):
                # Print the first 300 characters of the retrieved chunk
                print(f"  -> Retrieved Chunk {i+1} Preview:\n     {doc.page_content[:300].replace('\n', ' ')}")
            print("-" * 70)
print("=" * 70)
print(f"  ✅ Results saved to: {csv_path}")
print("=" * 70)
