import subprocess
from langchain.tools import tool


@tool
def format_and_lint_python(code: str) -> str:
    """Format and lint Python code using Ruff."""
    # Write code to a temp file or run via stdin
    process = subprocess.run(
        ["ruff", "check", "--fix", "-"],
        input=code,
        text=True,
        capture_output=True,
    )
    return process.stdout or process.stderr
