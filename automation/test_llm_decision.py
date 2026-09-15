from playwright.sync_api import sync_playwright

from automation.discovery_llm import choose_next_action
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

        observation = surface.observe()

        action = choose_next_action(
            goal,
            observation,
        )

        print(
            action.model_dump_json(
                indent=2
            )
        )

        browser.close()


if __name__ == "__main__":
    main()