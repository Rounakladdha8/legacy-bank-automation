from playwright.sync_api import sync_playwright

from automation.discovery_llm import choose_next_action
from automation.discovery_executor import execute_discovery_action
from automation.surface import WebSurface


def main():
    goal = (
        "Find member 12345 "
        "and return their savings balance."
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()
        surface = WebSurface(page)

        surface.open(
            "http://127.0.0.1:8000"
        )

        # STEP 1
        observation = surface.observe()

        action = choose_next_action(
            goal,
            observation,
        )

        print("LLM ACTION 1:")
        print(
            action.model_dump_json(
                indent=2
            )
        )

        execute_discovery_action(
            surface,
            action,
        )

        # Observe again after LLM action
        observation = surface.observe()

        print("\nOBSERVATION AFTER ACTION 1:")
        print(observation)

        # STEP 2
        action = choose_next_action(
            goal,
            observation,
        )

        print("\nLLM ACTION 2:")
        print(
            action.model_dump_json(
                indent=2
            )
        )

        execute_discovery_action(
            surface,
            action,
        )

        print("\nOBSERVATION AFTER ACTION 2:")
        print(
            surface.observe()
        )

        input(
            "\nPress Enter to close browser..."
        )

        browser.close()


if __name__ == "__main__":
    main()