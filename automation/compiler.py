import json
from pathlib import Path

from automation.models import CapabilityArtifact


def compile_discovery_to_artifact(
    discovery_result: dict,
    member_id: str,
    output_path: str,
):
    if discovery_result.get("status") != "success":
        raise ValueError(
            "Only successful discovery runs can be compiled."
        )

    artifact_steps = []

    # ---------------------------------------
    # Initial navigation
    # ---------------------------------------

    artifact_steps.append(
        {
            "step_id": "open_search",
            "action": "navigate",
            "value": "http://127.0.0.1:8000",
            "target": None,
            "checkpoint": {
                "type": "text_present",
                "expected": "Member Search",
            },
            "retry": {
                "max_attempts": 2,
                "wait_seconds": 1,
            },
            "risk": "safe",
        }
    )

    # ---------------------------------------
    # Compile discovered trajectory
    # ---------------------------------------

    for item in discovery_result["history"]:
        action = item["action"]
        value = item.get("value")
        step_number = item["step"]

        execution_result = (
            item.get("execution_result")
            or {}
        )

        locator = execution_result.get(
            "locator"
        )

        # -------------------------
        # FILL
        # -------------------------

        if action == "fill":
            if locator is None:
                raise ValueError(
                    "Successful fill action has "
                    "no recorded locator."
                )

            if value == member_id:
                value = "{{member_id}}"

            artifact_steps.append(
                {
                    "step_id": (
                        f"discovered_{step_number}_fill"
                    ),
                    "action": "fill",
                    "target": locator,
                    "value": value,
                    "retry": {
                        "max_attempts": 2,
                        "wait_seconds": 1,
                    },
                    "checkpoint": None,
                    "risk": "safe",
                }
            )

        # -------------------------
        # CLICK
        # -------------------------

        elif action == "click":
            if locator is None:
                raise ValueError(
                    "Successful click action has "
                    "no recorded locator."
                )

            artifact_steps.append(
                {
                    "step_id": (
                        f"discovered_{step_number}_click"
                    ),
                    "action": "click",
                    "target": locator,
                    "value": None,
                    "retry": {
                        "max_attempts": 2,
                        "wait_seconds": 1,
                    },
                    "checkpoint": None,
                    "risk": "safe",
                }
            )

        # -------------------------
        # EXTRACT
        # -------------------------

        elif action == "extract":
            if locator is None:
                raise ValueError(
                    "Successful extraction has "
                    "no stable recorded locator."
                )

            artifact_steps.append(
                {
                    "step_id": (
                        f"discovered_{step_number}_extract"
                    ),
                    "action": "extract",
                    "target": locator,
                    "value": None,
                    "retry": {
                        "max_attempts": 2,
                        "wait_seconds": 1,
                    },
                    "checkpoint": {
                        "type": "text_present",
                        "expected": (
                            item.get("target")
                            or "Available Balance"
                        ),
                    },
                    "risk": "safe",
                }
            )

        # -----------------------------------
        # CLICK
        # -----------------------------------

        elif action == "click":
            if target == "Search":
                strategy = "role_button"

            elif target == "View Savings":
                strategy = "role_link"

            else:
                raise ValueError(
                    "Compiler does not know how to "
                    f"represent click target: {target}"
                )

            artifact_steps.append(
                {
                    "step_id": (
                        f"discovered_{step_number}_click"
                    ),
                    "action": "click",
                    "value": None,
                    "target": {
                        "strategy": strategy,
                        "value": target,
                    },
                    "checkpoint": None,
                    "retry": {
                        "max_attempts": 2,
                        "wait_seconds": 1,
                    },
                    "risk": "safe",
                }
            )

        # -----------------------------------
        # EXTRACT
        # -----------------------------------

        elif action == "extract":
            artifact_steps.append(
                {
                    "step_id": (
                        f"discovered_{step_number}_extract"
                    ),
                    "action": "extract",
                    "value": None,
                    "target": {
                        "strategy": "css",
                        "value": "#savings-balance",
                    },
                    "checkpoint": {
                        "type": "text_present",
                        "expected": "Available Balance",
                    },
                    "retry": {
                        "max_attempts": 2,
                        "wait_seconds": 1,
                    },
                    "risk": "safe",
                }
            )

    # ---------------------------------------
    # Build artifact using ACTUAL schema
    # ---------------------------------------

    artifact = {
        "schema_version": "1.0",
        "capability_id": "get_savings_balance",
        "name": "Get Savings Balance",
        "version": "1.0",

        "description": (
            "Find a LegacyBank member and return "
            "their savings balance."
        ),

        "inputs": [
            {
                "name": "member_id",
                "type": "string",
                "required": True,
            }
        ],

        "outputs": [
            {
                "name": "savings_balance",
                "type": "string",
            }
        ],

        "steps": artifact_steps,

        "success_condition": {
            "type": "output_present",
            "expected": "savings_balance",
        },
    }

    # ---------------------------------------
    # Validate artifact
    # ---------------------------------------

    validated_artifact = (
        CapabilityArtifact.model_validate(
            artifact
        )
    )

    artifact = validated_artifact.model_dump(
        mode="json"
    )

    # ---------------------------------------
    # Save only AFTER validation succeeds
    # ---------------------------------------

    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            artifact,
            file,
            indent=2,
        )

    return artifact