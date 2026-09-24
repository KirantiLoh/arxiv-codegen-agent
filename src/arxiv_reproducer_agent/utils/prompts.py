from pathlib import Path


def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from a markdown file.

    Args:
        prompt_name: Name of the prompt file (without .md extension)
                     e.g., "ARCHITECT_AGENT" or "DEVELOPER_AGENT"

    Returns:
        The prompt text content
    """
    current_dir = Path(__file__).parent.parent
    prompt_file = current_dir / f"prompts/{prompt_name}.md"

    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    return prompt_file.read_text(encoding="utf-8")
