from langchain_classic.retrievers import MultiVectorRetriever
from qdrant_client import models

from arxiv_reproducer_agent.state import AgentState

def get_retriever_node(retriever: MultiVectorRetriever, top_k: int = 5):

    def retriever_node(state: AgentState) -> dict:
        query = state["user_query"]
        arxiv_id = state["arxiv_id"]
        
        try:
            qdrant_filter = models.Filter(must=[
                models.FieldCondition(
                    key="metadata.arxiv_id", match=models.MatchValue(value=arxiv_id)
                )
            ])

            # STEP 1: Search the CHILD vectorstore with the metadata filter
            child_results = retriever.vectorstore.similarity_search(
                query=query,
                filter=qdrant_filter,
                k=top_k,
            )

            if not child_results:
                return {
                        "error_message": f"No relevant information found in paper {arxiv_id} for this query."
            }
            # STEP 2: Extract unique parent_ids from the matching children
            parent_ids: list[str] = []
            for doc in child_results:
                pid = doc.metadata.get("parent_id")
                if pid is not None:
                    parent_ids.append(str(pid))

            # Remove duplicates
            parent_ids = list(set(parent_ids))

            # STEP 3: Fetch the full PARENT documents from the Redis docstore
            raw_parent_docs = retriever.docstore.mget(parent_ids)

            parent_docs = [doc for doc in raw_parent_docs if doc is not None]

            if not parent_docs:
                return f"Error: Found child chunks but could not retrieve parent documents for {arxiv_id}."

            # STEP 4: Format the parent documents cleanly for the LLM
            formatted_results = []
            for i, doc in enumerate(parent_docs):
                section = doc.metadata.get("section", "Unknown Section")
                subsection = doc.metadata.get("subsection", "")
                header = f"Section: {section}" + \
                    (f" | Subsection: {subsection}" if subsection else "")

                formatted_results.append(
                    f"### Context Chunk {i+1} ({header})\n{doc.page_content}"
                )

            return {
                    "retrieval_context": "\n\n---\n\n".join(formatted_results),
            }

        except Exception as e:
            error_message = f"An error occurred during the search: {str(e)}"
            print(error_message)
            return {
                "error_message": error_message
            }


    return retriever_node
