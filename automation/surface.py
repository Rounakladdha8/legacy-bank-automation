from playwright.sync_api import Page


class WebSurface:
    def __init__(self, page: Page):
        self.page = page

    # -----------------------------------
    # Navigation
    # -----------------------------------

    def open(self, url: str):
        self.page.goto(url)

    # -----------------------------------
    # Form interaction
    # -----------------------------------

    def fill_by_label(
        self,
        label: str,
        value: str,
    ):
        self.page.get_by_label(
            label
        ).fill(value)

    # -----------------------------------
    # Click interaction
    # -----------------------------------

    def click_button(
        self,
        name: str,
    ):
        self.page.get_by_role(
            "button",
            name=name,
        ).click()

    def click_link(
        self,
        name: str,
    ):
        self.page.get_by_role(
            "link",
            name=name,
        ).click()

    # -----------------------------------
    # Basic reading
    # -----------------------------------

    def read_text(
        self,
        selector: str,
    ) -> str:
        return self.page.locator(
            selector
        ).inner_text()

    def has_text(
        self,
        text: str,
    ) -> bool:
        return (
            self.page.get_by_text(
                text,
                exact=False,
            ).count()
            > 0
        )

    # -----------------------------------
    # Screenshots
    # -----------------------------------

    def save_screenshot(
        self,
        path: str,
    ):
        self.page.screenshot(
            path=path,
            full_page=True,
        )

    # -----------------------------------
    # Generic extraction resolver
    # -----------------------------------

    def resolve_text_value(
        self,
        label_text: str,
    ) -> dict:
        """
        Resolve a visible value associated with
        a visible label.

        Preference:

        1. Explicit data-output relationship
        2. Nearby sibling with a stable ID
        3. Nearby visible sibling
        """

        # Find the visible label requested
        # by the discovery model.
        label = self.page.get_by_text(
            label_text,
            exact=True,
        )

        if label.count() == 0:
            raise ValueError(
                "Visible extraction label "
                f"not found: {label_text}"
            )

        label = label.first

        # -----------------------------------
        # Strategy 1:
        # Explicit data-output relationship
        # -----------------------------------

        data_output = (
            label.get_attribute(
                "data-output"
            )
        )

        if data_output:
            selector = (
                '[data-output-value="'
                f'{data_output}'
                '"]'
            )

            target = self.page.locator(
                selector
            )

            if target.count() > 0:
                target = target.first

                text = (
                    target
                    .inner_text()
                    .strip()
                )

                if text:
                    return {
                        "text": text,
                        "locator": {
                            "strategy": "css",
                            "value": selector,
                        },
                    }

        # -----------------------------------
        # Strategy 2:
        # Nearby sibling with stable ID
        # -----------------------------------

        sibling_with_id = (
            label.locator(
                "xpath="
                "following-sibling::*"
                "[@id][1]"
            )
        )

        if sibling_with_id.count() > 0:
            sibling = (
                sibling_with_id.first
            )

            element_id = (
                sibling.get_attribute(
                    "id"
                )
            )

            text = (
                sibling
                .inner_text()
                .strip()
            )

            if element_id and text:
                return {
                    "text": text,
                    "locator": {
                        "strategy": "css",
                        "value": (
                            f"#{element_id}"
                        ),
                    },
                }

        # -----------------------------------
        # Strategy 3:
        # Nearby visible sibling
        # -----------------------------------

        sibling = label.locator(
            "xpath="
            "following-sibling::*[1]"
        )

        if sibling.count() > 0:
            sibling = sibling.first

            text = (
                sibling
                .inner_text()
                .strip()
            )

            if text:
                element_id = (
                    sibling.get_attribute(
                        "id"
                    )
                )

                # We found the value and it
                # also has a stable ID.
                if element_id:
                    return {
                        "text": text,
                        "locator": {
                            "strategy": "css",
                            "value": (
                                f"#{element_id}"
                            ),
                        },
                    }

                # Value exists, but there is
                # no stable locator suitable
                # for deterministic replay.
                return {
                    "text": text,
                    "locator": None,
                }

        raise ValueError(
            "Could not resolve a value "
            "associated with visible label: "
            f"{label_text}"
        )

    # -----------------------------------
    # UI observation for discovery
    # -----------------------------------

    def observe(self) -> dict:
        controls = []

        # Observe input fields
        for element in (
            self.page.locator(
                "input"
            ).all()
        ):
            controls.append(
                {
                    "type": "input",
                    "name": (
                        element.get_attribute(
                            "name"
                        )
                    ),
                    "value": (
                        element.input_value()
                    ),
                    "placeholder": (
                        element.get_attribute(
                            "placeholder"
                        )
                    ),
                }
            )

        # Observe buttons
        for element in (
            self.page.get_by_role(
                "button"
            ).all()
        ):
            controls.append(
                {
                    "type": "button",
                    "text": (
                        element.inner_text()
                    ),
                }
            )

        # Observe links
        for element in (
            self.page.get_by_role(
                "link"
            ).all()
        ):
            controls.append(
                {
                    "type": "link",
                    "text": (
                        element.inner_text()
                    ),
                    "href": (
                        element.get_attribute(
                            "href"
                        )
                    ),
                }
            )

        return {
            "url": self.page.url,
            "title": self.page.title(),
            "text": (
                self.page.locator(
                    "body"
                ).inner_text()
            ),
            "controls": controls,
        }