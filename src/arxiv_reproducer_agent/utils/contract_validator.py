import re
from typing import List, Tuple
from arxiv_reproducer_agent.schemas.architect import (
    ArchitectOutput,
    FileDefinition,
    ClassDefinition,
    FunctionSignature
)


def validate_architect_contract(contract: ArchitectOutput) -> Tuple[bool, List[str]]:
    """
    Pure Python validation of the Architect's JSON contract.
    Returns (is_valid, list_of_errors).
    """
    errors = []

    # 1. Extract all valid filenames for internal dependency checking
    valid_filenames = {f.filename for f in contract.files}

    for file_def in contract.files:
        # --- File Level Checks ---
        if not file_def.filename.endswith(".py"):
            errors.append(f"File '{file_def.filename}' must end with .py")
        if " " in file_def.filename:
            errors.append(f"File '{file_def.filename}' cannot contain spaces.")

        if not file_def.classes and not file_def.functions:
            errors.append(
                f"File '{file_def.filename}' is empty (no classes or functions defined)."
            )

        # --- Import Checks ---
        for imp in file_def.imports:
            if not imp.strip():
                errors.append(
                    f"File '{file_def.filename}' contains an empty import string."
                )
            elif not re.match(r'^[a-zA-Z0-9_\s\.]+$', imp):
                errors.append(
                    f"File '{file_def.filename}' has an invalid import format: '{imp}'"
                )

        # --- Class Level Checks ---
        for class_def in file_def.classes:
            if not re.match(r'^[A-Z][a-zA-Z0-9_]*$', class_def.name):
                errors.append(
                    f"Class '{class_def.name}' in '{file_def.filename}' should be PascalCase (e.g., LoadPredictor)."
                )

            for method in class_def.methods:
                _validate_function(method, file_def.filename, errors)

            # Check attributes format flexibly
            for attr in class_def.attributes:
                attr_name = attr.get("name") or attr.get("attribute_name") or attr.get("param_name")
                attr_type = attr.get("type") or attr.get("data_type")
                
                # If it's a single key-value dict like {"cpu_utilization": "float"}
                if not attr_name and len(attr) == 1:
                    attr_name, attr_type = list(attr.items())[0]

                if not attr_name:
                    errors.append(
                        f"Attribute in class '{class_def.name}' is missing a name key ('name' or 'attribute_name')."
                    )

        # --- Standalone Function Checks ---
        for func_def in file_def.functions:
            _validate_function(func_def, file_def.filename, errors)

    # 2. Dependency Graph Integrity Checks
    for file_name, deps in contract.dependencies.items():
        if file_name not in valid_filenames:
            errors.append(
                f"Dependency error: '{file_name}' is listed in dependencies but not in the 'files' list."
            )

        for dep in deps:
            # FIX: Only validate internal dependencies (files ending in .py)
            if dep.endswith(".py"):
                if dep not in valid_filenames:
                    errors.append(
                        f"Dependency error: '{file_name}' depends on internal file '{dep}', which does not exist in 'files'."
                    )
                if dep == file_name:
                    errors.append(
                        f"Dependency error: '{file_name}' cannot depend on itself."
                    )

    return len(errors) == 0, errors


def _validate_function(func: FunctionSignature, filename: str, errors: List[str]):
    """Helper to validate function signatures."""
    # Function naming (snake_case)
    if not re.match(r'^[a-z_][a-z0-9_]*$', func.name):
        errors.append(
            f"Function '{func.name}' in '{filename}' should be snake_case (e.g., calculate_load)."
        )

    # Parameter validation
    for param in func.parameters:
        param_name = param.get("name") or param.get("param_name") or param.get("attribute_name")
        
        # Support dict mapping like {"param_one": "str"}
        if not param_name and len(param) == 1:
            param_name = list(param.keys())[0]

        if not param_name:
            errors.append(
                f"Parameter in function '{func.name}' is missing a name key ('name' or 'param_name')."
            )
        elif not re.match(r'^[a-z_][a-z0-9_]*$', str(param_name)):
            errors.append(
                f"Parameter '{param_name}' in function '{func.name}' should be snake_case."
            )

    # Return type validation
    if not str(func.return_type).strip():
        errors.append(f"Function '{func.name}' is missing a return type.")
