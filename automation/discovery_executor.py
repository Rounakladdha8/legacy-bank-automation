from automation.discovery_models import (
    DiscoveryAction,
    DiscoveryActionType,
)
from automation.surface import WebSurface


def execute_discovery_action(
    surface: WebSurface,
    action: DiscoveryAction,
):
    # -------------------------
    # FILL
    # -------------------------

    if action.action == DiscoveryActionType.FILL:
        if action.target is None or action.value is None:
            raise ValueError(
                "Fill action requires target and value."
            )

        surface.fill_by_label(
            action.target,
            action.value,
        )

        return {
            "locator": {
                "strategy": "label",
                "value": action.target,
            }
        }

    # -------------------------
    # CLICK
    # -------------------------

    if action.action == DiscoveryActionType.CLICK:
        if action.target is None:
            raise ValueError(
                "Click action requires a target."
            )

        # Try accessible button first.
        button = surface.page.get_by_role(
            "button",
            name=action.target,
        )

        if button.count() > 0:
            button.click()

            return {
                "locator": {
                    "strategy": "role_button",
                    "value": action.target,
                }
            }

        # Then try an accessible link.
        link = surface.page.get_by_role(
            "link",
            name=action.target,
        )

        if link.count() > 0:
            link.click()

            return {
                "locator": {
                    "strategy": "role_link",
                    "value": action.target,
                }
            }

        raise ValueError(
            f"Clickable target not found: {action.target}"
        )

    # -------------------------
    # EXTRACT
    # -------------------------

    if action.action == DiscoveryActionType.EXTRACT:
        if action.target is None:
            raise ValueError(
                "Extract action requires a target."
            )

        # Ask WebSurface to resolve the value
        # from the current page structure.
        resolved = surface.resolve_text_value(
            action.target
        )

        # Discovery may understand the value,
        # but compilation requires a stable
        # locator for deterministic replay.
        if resolved["locator"] is None:
            raise ValueError(
                "Extraction value was found, "
                "but no stable replay locator "
                "could be established."
            )

        return {
            "output_name": (
                action.output_name
                or "result"
            ),
            "output_value": (
                resolved["text"]
            ),
            "locator": (
                resolved["locator"]
            ),
        }

    # -------------------------
    # FINISH
    # -------------------------

    if action.action == DiscoveryActionType.FINISH:
        return {
            "finished": True,
            "output_name": action.output_name,
            "output_value": action.output_value,
        }

    # -------------------------
    # ESCALATE
    # -------------------------

    if action.action == DiscoveryActionType.ESCALATE:
        return {
            "escalate": True,
            "reason": action.reason,
        }

    raise ValueError(
        f"Unsupported discovery action: {action.action}"
    )