import json
import time
import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright

from automation.intervention import InterventionManager
from automation.logger import EvidenceLogger
from automation.models import (
    CapabilityArtifact,
    ReplayResult,
    ReplayStatus,
)
from automation.policy import PolicyGuard, PolicyViolation
from automation.surface import WebSurface


ARTIFACT_PATH = (
    "artifacts/discovered_get_savings_balance.json"
)


def load_artifact() -> CapabilityArtifact:
    with open(
        ARTIFACT_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return CapabilityArtifact.model_validate(
        data
    )


def resolve_value(
    value: str | None,
    member_id: str,
) -> str | None:
    if value is None:
        return None

    return value.replace(
        "{{member_id}}",
        member_id,
    )


def save_failure_screenshot(
    surface: WebSurface,
    run_id: str,
    step_id: str,
) -> str:
    Path("evidence").mkdir(
        parents=True,
        exist_ok=True,
    )

    screenshot_path = (
        f"evidence/"
        f"{run_id}-{step_id}.png"
    )

    surface.save_screenshot(
        screenshot_path
    )

    return screenshot_path


def run_replay(
    member_id: str,
) -> ReplayResult:
    artifact = load_artifact()

    run_id = (
        f"replay-"
        f"{uuid.uuid4().hex[:8]}"
    )

    logger = EvidenceLogger(
        run_id
    )

    logger.log(
        "run_started",
        capability_id=(
            artifact.capability_id
        ),
        member_id=member_id,
        mode="replay",
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        surface = WebSurface(page)

        policy = PolicyGuard()

        intervention = (
            InterventionManager(
                surface,
                logger,
            )
        )

        outputs = {}

        current_step_id = "startup"

        try:
            for step in artifact.steps:
                current_step_id = (
                    step.step_id
                )

                value = resolve_value(
                    step.value,
                    member_id,
                )

                logger.log(
                    "step_started",
                    step_id=(
                        step.step_id
                    ),
                    action=step.action,
                    risk=step.risk.value,
                )

                # --------------------
                # Safety checks
                # --------------------

                policy.check_action(
                    step.action,
                    step.risk,
                )

                if (
                    step.action
                    == "navigate"
                    and value
                    is not None
                ):
                    policy.check_url(
                        value
                    )

                attempts = 0

                while (
                    attempts
                    <
                    step.retry.max_attempts
                ):
                    attempts += 1

                    logger.log(
                        "attempt_started",
                        step_id=(
                            step.step_id
                        ),
                        attempt=attempts,
                    )

                    # --------------------
                    # Execute action
                    # --------------------

                    if (
                        step.action
                        == "navigate"
                    ):
                        surface.open(
                            value
                        )

                    elif (
                        step.action
                        == "fill"
                    ):
                        if (
                            step.target
                            is not None
                            and
                            step.target.strategy
                            == "label"
                        ):
                            surface.fill_by_label(
                                step.target.value,
                                value,
                            )

                    elif (
                        step.action
                        == "click"
                    ):
                        if (
                            step.target
                            is not None
                            and
                            step.target.strategy
                            == "role_button"
                        ):
                            surface.click_button(
                                step.target.value
                            )

                        elif (
                            step.target
                            is not None
                            and
                            step.target.strategy
                            == "role_link"
                        ):
                            surface.click_link(
                                step.target.value
                            )

                    elif (
                        step.action
                        == "extract"
                    ):
                        if (
                            step.target
                            is not None
                            and
                            step.target.strategy
                            == "css"
                        ):
                            text = (
                                surface
                                .read_text(
                                    step.target.value
                                )
                            )

                            outputs[
                                "savings_balance"
                            ] = text

                    # --------------------
                    # Human intervention
                    # --------------------

                    if surface.has_text(
                        "Manual Verification Required"
                    ):
                        screenshot_path = (
                            save_failure_screenshot(
                                surface,
                                run_id,
                                step.step_id,
                            )
                        )

                        logger.log(
                            "human_intervention_detected",
                            step_id=(
                                step.step_id
                            ),
                            reason=(
                                "Manual "
                                "verification "
                                "required"
                            ),
                            screenshot=(
                                screenshot_path
                            ),
                        )

                        intervention.request_handoff(
                            reason=(
                                "LegacyBank "
                                "requires "
                                "manual "
                                "verification."
                            ),
                            step_id=(
                                step.step_id
                            ),
                        )

                    # --------------------
                    # Business outcome
                    # --------------------

                    if surface.has_text(
                        "Member Not Found"
                    ):
                        screenshot_path = (
                            save_failure_screenshot(
                                surface,
                                run_id,
                                step.step_id,
                            )
                        )

                        logger.log(
                            "business_outcome",
                            step_id=(
                                step.step_id
                            ),
                            code=(
                                "MEMBER_NOT_FOUND"
                            ),
                            screenshot=(
                                screenshot_path
                            ),
                        )

                        result = (
                            ReplayResult(
                                status=(
                                    ReplayStatus
                                    .BUSINESS_OUTCOME
                                ),
                                code=(
                                    "MEMBER_NOT_FOUND"
                                ),
                                step_id=(
                                    step.step_id
                                ),
                                observed=(
                                    "Member Not Found"
                                ),
                                message=(
                                    "The member "
                                    "does not exist."
                                ),
                            )
                        )

                        logger.log(
                            "run_completed",
                            status=(
                                result
                                .status
                                .value
                            ),
                            code=(
                                result.code
                            ),
                        )

                        browser.close()

                        return result

                    # --------------------
                    # Hard failure
                    # --------------------

                    if surface.has_text(
                        "Permission Denied"
                    ):
                        screenshot_path = (
                            save_failure_screenshot(
                                surface,
                                run_id,
                                step.step_id,
                            )
                        )

                        logger.log(
                            "hard_failure",
                            step_id=(
                                step.step_id
                            ),
                            code=(
                                "PERMISSION_DENIED"
                            ),
                            screenshot=(
                                screenshot_path
                            ),
                        )

                        result = (
                            ReplayResult(
                                status=(
                                    ReplayStatus
                                    .HARD_FAILURE
                                ),
                                code=(
                                    "PERMISSION_DENIED"
                                ),
                                step_id=(
                                    step.step_id
                                ),
                                observed=(
                                    "Permission Denied"
                                ),
                                message=(
                                    "Access to this "
                                    "member is not "
                                    "permitted."
                                ),
                            )
                        )

                        logger.log(
                            "run_completed",
                            status=(
                                result
                                .status
                                .value
                            ),
                            code=(
                                result.code
                            ),
                        )

                        browser.close()

                        return result

                    # --------------------
                    # Recoverable state
                    # --------------------

                    if surface.has_text(
                        "System Busy"
                    ):
                        logger.log(
                            "recoverable_condition",
                            step_id=(
                                step.step_id
                            ),
                            code=(
                                "SYSTEM_BUSY"
                            ),
                            attempt=attempts,
                        )

                        if (
                            attempts
                            <
                            step.retry
                            .max_attempts
                        ):
                            logger.log(
                                "retry_scheduled",
                                step_id=(
                                    step.step_id
                                ),
                                next_attempt=(
                                    attempts + 1
                                ),
                                wait_seconds=(
                                    step.retry
                                    .wait_seconds
                                ),
                            )

                            time.sleep(
                                step.retry
                                .wait_seconds
                            )

                            continue

                        screenshot_path = (
                            save_failure_screenshot(
                                surface,
                                run_id,
                                step.step_id,
                            )
                        )

                        logger.log(
                            "recoverable_exhausted",
                            step_id=(
                                step.step_id
                            ),
                            code=(
                                "SYSTEM_BUSY"
                            ),
                            screenshot=(
                                screenshot_path
                            ),
                        )

                        result = (
                            ReplayResult(
                                status=(
                                    ReplayStatus
                                    .RECOVERABLE_CONDITION
                                ),
                                code=(
                                    "SYSTEM_BUSY"
                                ),
                                step_id=(
                                    step.step_id
                                ),
                                observed=(
                                    "System Busy"
                                ),
                                message=(
                                    "Retry limit "
                                    "reached while "
                                    "the system "
                                    "remained busy."
                                ),
                            )
                        )

                        logger.log(
                            "run_completed",
                            status=(
                                result
                                .status
                                .value
                            ),
                            code=(
                                result.code
                            ),
                        )

                        browser.close()

                        return result

                    # --------------------
                    # Checkpoint
                    # --------------------

                    if (
                        step.checkpoint
                        is not None
                    ):
                        expected = (
                            step.checkpoint
                            .expected
                        )

                        if not surface.has_text(
                            expected
                        ):
                            logger.log(
                                "checkpoint_failed",
                                step_id=(
                                    step.step_id
                                ),
                                expected=(
                                    expected
                                ),
                                attempt=(
                                    attempts
                                ),
                            )

                            if (
                                attempts
                                <
                                step.retry
                                .max_attempts
                            ):
                                time.sleep(
                                    step.retry
                                    .wait_seconds
                                )

                                continue

                            screenshot_path = (
                                save_failure_screenshot(
                                    surface,
                                    run_id,
                                    step.step_id,
                                )
                            )

                            logger.log(
                                "checkpoint_failure_final",
                                step_id=(
                                    step.step_id
                                ),
                                expected=(
                                    expected
                                ),
                                screenshot=(
                                    screenshot_path
                                ),
                            )

                            result = (
                                ReplayResult(
                                    status=(
                                        ReplayStatus
                                        .HARD_FAILURE
                                    ),
                                    code=(
                                        "CHECKPOINT_FAILED"
                                    ),
                                    step_id=(
                                        step.step_id
                                    ),
                                    expected=(
                                        expected
                                    ),
                                    observed=(
                                        "Expected "
                                        "text was "
                                        "not found."
                                    ),
                                    message=(
                                        "Replay reached "
                                        "an unexpected "
                                        "UI state."
                                    ),
                                )
                            )

                            logger.log(
                                "run_completed",
                                status=(
                                    result
                                    .status
                                    .value
                                ),
                                code=(
                                    result.code
                                ),
                            )

                            browser.close()

                            return result

                    logger.log(
                        "step_completed",
                        step_id=(
                            step.step_id
                        ),
                        attempt=(
                            attempts
                        ),
                    )

                    break

            # --------------------
            # Successful replay
            # --------------------

            result = ReplayResult(
                status=(
                    ReplayStatus.SUCCESS
                ),
                outputs=outputs,
                message=(
                    "Replay completed "
                    "successfully."
                ),
            )

            logger.log(
                "run_completed",
                status=(
                    result.status.value
                ),
            )

        # ------------------------
        # Safety violation
        # ------------------------

        except PolicyViolation as error:
            screenshot_path = (
                save_failure_screenshot(
                    surface,
                    run_id,
                    current_step_id,
                )
            )

            logger.log(
                "policy_violation",
                step_id=(
                    current_step_id
                ),
                message=(
                    str(error)
                ),
                screenshot=(
                    screenshot_path
                ),
            )

            result = ReplayResult(
                status=(
                    ReplayStatus
                    .HARD_FAILURE
                ),
                code=(
                    "POLICY_VIOLATION"
                ),
                step_id=(
                    current_step_id
                ),
                message=(
                    str(error)
                ),
            )

            logger.log(
                "run_completed",
                status=(
                    result.status.value
                ),
                code=(
                    result.code
                ),
            )

        # ------------------------
        # Unexpected failure
        # ------------------------

        except Exception as error:
            screenshot_path = (
                save_failure_screenshot(
                    surface,
                    run_id,
                    current_step_id,
                )
            )

            logger.log(
                "unexpected_error",
                step_id=(
                    current_step_id
                ),
                message=(
                    str(error)
                ),
                screenshot=(
                    screenshot_path
                ),
            )

            result = ReplayResult(
                status=(
                    ReplayStatus
                    .HARD_FAILURE
                ),
                code=(
                    "REPLAY_ERROR"
                ),
                step_id=(
                    current_step_id
                ),
                message=(
                    str(error)
                ),
            )

            logger.log(
                "run_completed",
                status=(
                    result.status.value
                ),
                code=(
                    result.code
                ),
            )

        browser.close()

        return result


if __name__ == "__main__":
    result = run_replay(
        "55555"
    )

    print(
        result.model_dump_json(
            indent=2
        )
    )