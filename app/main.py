from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.data import MEMBERS, SPECIAL_CASES


app = FastAPI()

# Serve CSS and other static assets.
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

templates = Jinja2Templates(
    directory="templates"
)


# Keeps track of temporary retry attempts
# for demo scenarios.
SEARCH_ATTEMPTS = {}


# -------------------------------------------------
# Member Search Page
# -------------------------------------------------

@app.get("/")
def search_page(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={},
    )


# -------------------------------------------------
# Member Search
# -------------------------------------------------

@app.get("/search")
def search_member(
    request: Request,
    member_id: str,
):

    # -------------------------------------------------
    # Recoverable condition
    #
    # First lookup for 88888 shows System Busy.
    # Second lookup succeeds.
    # -------------------------------------------------

    if member_id == "88888":
        attempts = SEARCH_ATTEMPTS.get(
            member_id,
            0,
        )

        if attempts == 0:
            SEARCH_ATTEMPTS[
                member_id
            ] = 1

            return templates.TemplateResponse(
                request=request,
                name="temporary_busy.html",
                context={
                    "member_id": member_id,
                },
            )

    # -------------------------------------------------
    # Hard failure
    #
    # Member 77777 simulates an authorization
    # failure that automation must not retry.
    # -------------------------------------------------

    if member_id == "77777":
        return RedirectResponse(
            url=(
                "/permission-denied"
                f"?member_id={member_id}"
            ),
            status_code=303,
        )

    # -------------------------------------------------
    # Human intervention
    #
    # Automation must pause when this page appears.
    # A human operator can perform the verification
    # step and then return control to automation.
    # -------------------------------------------------

    if member_id == "33333":
        return templates.TemplateResponse(
            request=request,
            name="manual_verification.html",
            context={
                "member_id": member_id,
            },
        )

    # -------------------------------------------------
    # Other special demo scenarios
    # -------------------------------------------------

    if (
        member_id in SPECIAL_CASES
        and member_id not in {
            "88888",
            "33333",
        }
    ):
        return {
            "status": "special_case",
            "member_id": member_id,
            "scenario": SPECIAL_CASES[
                member_id
            ],
        }

    # -------------------------------------------------
    # Legitimate business outcome
    #
    # A missing member is not a system failure.
    # -------------------------------------------------

    if member_id not in MEMBERS:
        return RedirectResponse(
            url=(
                "/member-not-found"
                f"?member_id={member_id}"
            ),
            status_code=303,
        )

    # -------------------------------------------------
    # Normal successful lookup
    # -------------------------------------------------

    return RedirectResponse(
        url=f"/member/{member_id}",
        status_code=303,
    )


# -------------------------------------------------
# Continue After Human Verification
# -------------------------------------------------

@app.get(
    "/manual-verification/continue"
)
def continue_after_verification(
    member_id: str,
):
    return RedirectResponse(
        url=f"/member/{member_id}",
        status_code=303,
    )


# -------------------------------------------------
# Member Profile
# -------------------------------------------------

@app.get("/member/{member_id}")
def member_page(
    request: Request,
    member_id: str,
):
    member = MEMBERS[
        member_id
    ]

    return templates.TemplateResponse(
        request=request,
        name="member.html",
        context={
            "member_id": member_id,
            "member": member,
        },
    )


# -------------------------------------------------
# Savings Account
# -------------------------------------------------

@app.get(
    "/member/{member_id}/savings"
)
def savings_page(
    request: Request,
    member_id: str,
):
    member = MEMBERS[
        member_id
    ]

    return templates.TemplateResponse(
        request=request,
        name="savings.html",
        context={
            "member_id": member_id,
            "member": member,
        },
    )


# -------------------------------------------------
# Member Not Found
# -------------------------------------------------

@app.get("/member-not-found")
def member_not_found_page(
    request: Request,
    member_id: str,
):
    return templates.TemplateResponse(
        request=request,
        name="not_found.html",
        context={
            "member_id": member_id,
        },
    )


# -------------------------------------------------
# Permission Denied
# -------------------------------------------------

@app.get("/permission-denied")
def permission_denied_page(
    request: Request,
    member_id: str,
):
    return templates.TemplateResponse(
        request=request,
        name="permission_denied.html",
        context={
            "member_id": member_id,
        },
    )