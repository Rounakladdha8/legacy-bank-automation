import os

from dotenv import load_dotenv
from openai import OpenAI

from automation.discovery_models import DiscoveryAction


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


SYSTEM_PROMPT = """
You are controlling a legacy banking web interface.

Your job is to choose exactly ONE next UI action
that moves toward the user's goal.

You may choose only these actions:

- fill
- click
- extract
- finish
- escalate

Rules:

1. Never invent UI elements that are not visible.

2. Choose only one action at a time.

3. Pay attention to INTERACTIVE CONTROLS.
   They show the current state of input fields,
   buttons, and links.

4. If an input already contains the required value,
   do NOT fill it again. Move to the next appropriate
   action.

5. For fill:
   - target should be the visible field label.
   - value should be the value to enter.

6. For click:
   - target should be the visible button or link text.

7. For extract:
   - target should describe the visible information to read.
   - output_name should describe the output.

8. Use finish only when the requested goal is complete.

9. Use escalate if the UI requires manual verification,
   risky approval, or a human decision.

10. Keep reason short and operational.
"""


def choose_next_action(
    goal: str,
    observation: dict,
) -> DiscoveryAction:

    prompt = f"""
GOAL:
{goal}

CURRENT UI:

URL:
{observation["url"]}

PAGE TITLE:
{observation["title"]}

VISIBLE TEXT:
{observation["text"]}

INTERACTIVE CONTROLS:
{observation.get("controls", [])}

PREVIOUS ACTIONS:
{observation.get("history", [])}

EXTRACTED DATA:
{observation.get("extracted_data", {})}

Choose the single next action.

Choose the single next action.
"""

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format=DiscoveryAction,
    )

    action = (
        response
        .choices[0]
        .message
        .parsed
    )

    if action is None:
        raise RuntimeError(
            "LLM did not return a valid DiscoveryAction."
        )

    return action