import os
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from arxiv_reproducer_agent.utils.prompts import load_prompt
from arxiv_reproducer_agent.state import AgentState


def get_guide_node():
    llm = ChatOllama(
        model="qwen2.5-coder:3b",
        temperature=0,
        num_ctx=4096, # Increased slightly to accommodate chat history
    )

    system_prompt_template = load_prompt("GUIDE_AGENT")

    def guide_node(state: AgentState) -> dict:
        mode = state.get("mode")
        query = state.get("user_query")
        
        # 1. Prepare Context based on Mode
        if mode == "dev":
            current_file = state.get("current_file_being_generated")
            generated_files = state.get("generated_files", {})
            file_content = generated_files.get(current_file, "No file content available.")
            
            context_str = f"Current File Being Generated: {current_file}\n\nFile Content:\n```python\n{file_content}\n```"
            
        elif mode == "qna":
            context_str = f"Retrieval Context:\n{state.get('retrieval_context', 'No context available.')}"

        # 2. Inject Context into System Prompt
        # We append the dynamic context to the base system prompt
        full_system_prompt = f"{system_prompt_template}\n\n{context_str}"
        system_message = SystemMessage(content=full_system_prompt)

        # 3. Manage Chat History (Multi-Turn Logic)
        messages = state.get("messages", [])
        
        if not messages or messages[-1].content != query:
            messages = messages + [HumanMessage(content=query)]
            
        messages = messages[-6:]

        response = llm.invoke([system_message] + messages)

        return {
            "messages": [AIMessage(content=response.content)]
        }

    return guide_node
