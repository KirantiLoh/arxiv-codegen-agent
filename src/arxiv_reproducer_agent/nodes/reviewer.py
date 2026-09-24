# nodes/reviewer.py
import ast
from arxiv_reproducer_agent.state import AgentState


def reviewer_node(state: AgentState) -> dict:
    """
    Deterministically checks the generated code for syntax errors 
    and basic contract adherence.
    """
    generated_files = state.get("generated_files", {})
    contract = state.get("architect_contract", {})
    feedback = []

    for filename, code in generated_files.items():
        # 1. Syntax Check
        try:
            ast.parse(code)
        except SyntaxError as e:
            feedback.append(
                f"❌ {filename}: Syntax Error at line {e.lineno} - {e.msg}")

        # 2. Basic Contract Check (Did it create the classes?)
        file_contract = next((f for f in contract.get(
            "files", []) if f["filename"] == filename), None)
        if file_contract:
            for class_def in file_contract.get("classes", []):
                if f"class {class_def['name']}" not in code:
                    feedback.append(
                        f"️ {filename}: Missing class '{class_def['name']}' defined in contract.")

    if feedback:
        return {
            "contract_is_valid": False,  # Reuse this flag for code validity
            "contract_feedback": "Code Review Failed:\n" + "\n".join(feedback)
        }

    return {
        "contract_is_valid": True,
        "contract_feedback": "Code passed deterministic review."
    }
