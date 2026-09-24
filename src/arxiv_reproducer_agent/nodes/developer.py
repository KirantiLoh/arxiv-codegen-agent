import os
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from arxiv_reproducer_agent.utils.prompts import load_prompt
from arxiv_reproducer_agent.state import AgentState


def clean_code_snippet(text: str) -> str:
    """Strips markdown code fences (```python ... ```) to return raw code."""
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
    if text.endswith("```"):
        text = text[:-3].rstrip()
    return text.strip()


def get_developer_node(dir_path: str):
    llm = ChatOllama(
        model="qwen2.5-coder:3b",
        temperature=0,
        num_ctx=3072,
    )

    system_prompt = load_prompt("DEVELOPER_AGENT")

    def developer_node(state: AgentState) -> dict:
        contract = state.get("architect_contract")
        if not contract:
            return {"contract_feedback": "Critical: No architect contract found."}

        files_list = contract.get("files", [])
        generated_files = state.get("generated_files") or {}

        # 1. Filter out files that are already generated
        files_to_build = [
            f for f in files_list if f.get("filename") not in generated_files
        ]

        # Base case: All files are done
        if not files_to_build:
            return {"generated_files": generated_files}

        current_file_def = files_to_build[0]
        filename = current_file_def.get("filename", "output.py")

        # 2. Prompt LLM to generate code for current file
        user_content = (
            f"### FILE DEFINITION CONTRACT:\n{current_file_def}\n\n"
            f"### FULL CONTRACT CONFIGURATION:\n{contract.get('configuration', {})}\n\n"
            f"### ALGORITHM FLOW:\n{contract.get('algorithm_flow', [])}\n\n"
            f"CRITICAL: Generate the complete Python implementation for '{filename}'. "
            f"Output ONLY executable Python code with no explanations or markdown headers outside code."
        )

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ])

        generated_code = clean_code_snippet(response.content)

        # 3. WRITE FILE TO DISK
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(generated_code)

        # 4. Update State
        generated_files[filename] = generated_code

        return {
            "generated_files": generated_files,
            "current_file_being_generated": filename,
        }

    return developer_node
