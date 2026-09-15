from playwright.sync_api import sync_playwright

from automation.surface import WebSurface


def main():
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

        print(observation)

        browser.close()


if __name__ == "__main__":
    main()