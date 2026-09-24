# nodes/validator.py
from arxiv_reproducer_agent.schemas.architect import ArchitectOutput
from arxiv_reproducer_agent.state import AgentState
from arxiv_reproducer_agent.utils.contract_validator import (
    validate_architect_contract,
)


def get_validator_node():
    def validate_contract_node(state: AgentState) -> dict:
        """Deterministically validates the Architect's contract."""
        architect_contract = state.get("architect_contract")

        if not architect_contract:
            return {
                "contract_is_valid": False,
                "contract_feedback": "Contract was not created.",
            }

        if (
            isinstance(architect_contract, dict)
            and "ArchitectOutput" in architect_contract
        ):
            architect_contract = architect_contract["ArchitectOutput"]

        try:
            if isinstance(architect_contract, ArchitectOutput):
                contract = architect_contract
            else:
                contract = ArchitectOutput(**architect_contract)
        except Exception as e:
            return {
                "contract_is_valid": False,
                "contract_feedback": f"CRITICAL: The contract does not match Pydantic structure: {str(e)}",
            }

        # 3. Run deterministic checks
        is_valid, errors = validate_architect_contract(contract)

        if not is_valid:
            feedback = (
                "The following structural errors were found in your contract:\n"
                + "\n".join([f"- {e}" for e in errors])
            )
            return {
                "contract_is_valid": False,
                "contract_feedback": feedback,
            }

        return {"contract_is_valid": True, "contract_feedback": ""}

    return validate_contract_node
