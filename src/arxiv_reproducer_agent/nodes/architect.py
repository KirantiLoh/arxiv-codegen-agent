import json
import re
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from arxiv_reproducer_agent.utils.prompts import load_prompt
from arxiv_reproducer_agent.schemas.architect import ArchitectOutput
from arxiv_reproducer_agent.state import AgentState

def clean_json_string(text: str) -> str:
    """Removes markdown code fences (```json ... ```) from LLM output."""
    pattern = r"```(?:json)?\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def get_architect_node():
    # Direct LLM instance without middleware/tools interfering with output format
    llm = ChatOllama(
        model="qwen2.5-coder:3b",
        temperature=0,
        num_ctx=3072,  # Enforce lower context buffer to keep VRAM latency fast
    )

    system_prompt = load_prompt("ARCHITECT_AGENT")

    def architect_node(state: AgentState) -> dict:
        query = state.get("user_query", "")
        retrieval_context = state.get("retrieval_context", "")
        feedback = state.get("contract_feedback", "")

        # Truncate context if it exceeds 1500 chars to save generation latency
        truncated_context = retrieval_context[:2500] if len(retrieval_context) > 2500 else retrieval_context

        user_content = f"### CONTEXT:\n{truncated_context}\n\n### USER QUERY:\n{query}"
        if feedback:
            user_content += f"\n\n### PREVIOUS ERROR FEEDBACK:\n{feedback}"

        user_content += "\n\nCRITICAL: Respond ONLY with a raw JSON object matching the ArchitectOutput schema. Do NOT include introductory text or markdown commentary."

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ])

        cleaned_text = clean_json_string(response.content)
        contract_dict = None

        # Parse JSON output safely
        try:
            parsed_json = json.loads(cleaned_text)
            
            # If the LLM returned a wrapped dict, ensure Pydantic validation
            try:
                contract_dict = ArchitectOutput(**parsed_json).model_dump()
            except Exception:
                contract_dict = parsed_json
        except (json.JSONDecodeError, TypeError):
            contract_dict = None

        return {
            "architect_contract": contract_dict,
            "contract_feedback": "" if contract_dict else f"Failed to parse architect contract JSON. Raw output received:\n{response.content[:150]}..."
        }

    return architect_node
