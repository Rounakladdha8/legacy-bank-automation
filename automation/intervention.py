from automation.logger import EvidenceLogger
from automation.surface import WebSurface


class InterventionManager:
    def __init__(
        self,
        surface: WebSurface,
        logger: EvidenceLogger,
    ):
        self.surface = surface
        self.logger = logger

    def request_handoff(
        self,
        reason: str,
        step_id: str,
    ):
        self.logger.log(
            "human_handoff_requested",
            reason=reason,
            step_id=step_id,
        )

        print()
        print("=== HUMAN INTERVENTION REQUIRED ===")
        print(f"Reason: {reason}")
        print()
        print("Available commands:")
        print("  click <text>")
        print("  resume")
        print()

        while True:
            command = input("operator> ").strip()

            if command.lower() == "resume":
                self.logger.log(
                    "human_handoff_completed",
                    step_id=step_id,
                )

                print("Returning control to automation.")
                break

            if command.lower().startswith("click "):
                target_text = command[6:].strip()

                self.surface.page.get_by_text(
                    target_text,
                    exact=True,
                ).click()

                self.logger.log(
                    "human_action",
                    step_id=step_id,
                    action="click",
                    target=target_text,
                )

                print(
                    f"Human clicked: {target_text}"
                )

            else:
                print(
                    "Unknown command. "
                    "Use: click <text> or resume"
                )