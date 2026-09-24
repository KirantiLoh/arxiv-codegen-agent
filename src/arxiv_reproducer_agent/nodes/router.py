import laya 
from laya import Router
from arxiv_reproducer_agent.state import AgentState

def create_router_node(router: Router):

    def router_node(state: AgentState) -> dict:
        messages = state.get("messages", [])
        last_message = messages[-1]

        # Handle both LangChain Message objects and plain tuples
        if isinstance(last_message, tuple):
            query = last_message[1]
        elif hasattr(last_message, "content"):
            query = last_message.content
        else:
            query = str(last_message)

        questions = {
            "intent": {
                "type": "choice",
                "instructions": "Based on the user's query, determine the user's intent",
                "criteria": {
                    "qna": "Queries seeking conceptual explanations, factual recall, theoretical/mathematical formulations, design rationales, or comparative analyses that require natural language answers without asking to write, execute, or debug code.",
                    "dev": "Queries requesting actionable programmatic tasks, such as writing or refactoring code, debugging explicit errors or tracebacks, applying specific library/API syntax, or setting up software/framework pipelines.",
                }
            }
        }
        
        payload = {"query": query}
        res = router.predict(payload, questions)

        return {
            "mode": res["answers"]["intent"]["choice"],
            "user_query": query,
        }

    return router_node
