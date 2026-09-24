from typing import Dict, Any, Optional
from langgraph.graph import MessagesState


class AgentState(MessagesState):
    # --- Core Inputs ---
    arxiv_id: str
    user_query: Optional[str]
    mode: Optional[str]  # "codegen" or "qa"

    # --- Persistent Memory (The "Contract" & Results) ---
    # The JSON output from Architect
    architect_contract: Optional[Dict[str, Any]]
    generated_files: Optional[Dict[str, str]]     # {"filename.py": "code..."}

    # --- Ephemeral Data (Cleared/Updated per step) ---
    current_file_being_generated: Optional[str]   # e.g., "load_predictor.py"
    # String of retrieved chunks for the current step
    retrieval_context: Optional[str]
    # Error messages from Reviewer to Developer
    feedback_message: Optional[str]
    # Explicit boolean flag for the Reviewer node
    is_code_valid: Optional[bool]

    contract_is_valid: Optional[bool]
    contract_feedback: Optional[str]

    error_message: Optional[str]
    retry_count: int
