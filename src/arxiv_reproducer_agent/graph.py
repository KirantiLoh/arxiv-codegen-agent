import os

from langgraph.graph import StateGraph, START, END
from langchain_classic.retrievers import MultiVectorRetriever
import laya
from laya import Router

from arxiv_reproducer_agent.nodes.router import create_router_node
from arxiv_reproducer_agent.nodes.retriever import get_retriever_node
from arxiv_reproducer_agent.nodes.architect import get_architect_node
from arxiv_reproducer_agent.nodes.developer import get_developer_node
from arxiv_reproducer_agent.nodes.validator import get_validator_node
from arxiv_reproducer_agent.state import AgentState


def route_after_validation(state: AgentState):
    if state.get("contract_is_valid"):
        return "developer"
    else:
        return "architect"


def should_continue_developing(state: AgentState) -> str:
    """
    Checks if there are still files left to generate in the contract.
    """
    contract = state.get("architect_contract", {})
    generated_files = state.get("generated_files") or {}

    assert contract is not None
    total_files = len(contract.get("files", []))
    generated_count = len(generated_files)

    print(f"📊 Progress: Generated {generated_count} / {total_files} files.")

    # If we haven't generated all files yet, loop back to developer
    if generated_count < total_files:
        return "continue"

    # Otherwise, we are done
    return "end"


def create_workflow(retriever: MultiVectorRetriever, dir_path: str, laya_router: Router, top_k=5):
    workflow = StateGraph(AgentState)
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    
    router_node = create_router_node(laya_router)
    retriever_node = get_retriever_node(retriever, top_k)
    architect_agent = get_architect_node()
    developer_agent = get_developer_node(dir_path)
    validator_node = get_validator_node()

    # Define the states and transitions
    workflow.add_node("router", router_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("architect", architect_agent)
    workflow.add_node("validate_contract", validator_node)
    workflow.add_node("developer", developer_agent)

    # Define transitions between states
    workflow.add_edge(START, "router")
    workflow.add_edge("router", "retriever")
    workflow.add_edge("retriever", "architect")
    workflow.add_edge("architect","validate_contract")
    workflow.add_conditional_edges(
        "validate_contract",
        route_after_validation,
        {
            "developer": "developer",
            "architect": "architect"
        }
    )
    workflow.add_conditional_edges(
        "developer",
        should_continue_developing,
        {
            "continue": "developer",  # Loop back to generate the next file
            "end": END               # All files generated, finish the graph
        }
    )

    return workflow.compile()


if __name__ == "__main__":
    from qdrant_client import QdrantClient
    from laya import Router
    from langchain_community.storage import RedisStore
    from langchain_classic.storage._lc_store import create_kv_docstore
    from langchain_classic.retrievers import MultiVectorRetriever

    from utils.env import EnvConfig
    from utils.db import init_qdrant_vector_store
    
    env_config = EnvConfig()

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

    router = Router(preload=True)
    graph = create_workflow(retriever, ".", router, 2)
    inputs = {
        "messages": [("user", "Implement the load testing script in locust python")], 
        "arxiv_id": "2407.10173v1",
    }

    for update in graph.stream(inputs, stream_mode="updates"):
        # update format: { "node_name": { "state_key": "new_value" } }
        for node_name, node_output in update.items():
            print(f"\n🎬 Node finished running: [{node_name}]")
            print(f"Output: {node_output}")
