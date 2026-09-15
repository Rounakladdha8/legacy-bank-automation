from playwright.sync_api import sync_playwright

from automation.surface import WebSurface


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        surface = WebSurface(page)

        surface.open("http://127.0.0.1:8000")

        surface.fill_by_label(
            "Member ID",
            "12345",
        )

        surface.click_button("Search")

        surface.click_link("View Savings")

        balance = surface.read_text(
            "#savings-balance"
        )

        print("Savings balance:", balance)

        browser.close()


if __name__ == "__main__":
    main()