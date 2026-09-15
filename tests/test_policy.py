import pytest

from automation.models import RiskLevel
from automation.policy import (
    PolicyGuard,
    PolicyViolation,
)


def test_localhost_url_is_allowed():
    guard = PolicyGuard()

    # Should not raise an exception.
    guard.check_url(
        "http://127.0.0.1:8000"
    )


def test_external_domain_is_blocked():
    guard = PolicyGuard()

    with pytest.raises(
        PolicyViolation,
        match="Domain not allowed",
    ):
        guard.check_url(
            "https://example.com"
        )


def test_safe_action_is_allowed():
    guard = PolicyGuard()

    # Safe click should be permitted.
    guard.check_action(
        "click",
        RiskLevel.SAFE,
    )


def test_unknown_action_is_blocked():
    guard = PolicyGuard()

    with pytest.raises(
        PolicyViolation,
        match="Action not allowed",
    ):
        guard.check_action(
            "delete_account",
            RiskLevel.SAFE,
        )


def test_risky_action_requires_human_approval():
    guard = PolicyGuard()

    with pytest.raises(
        PolicyViolation,
        match="Human approval required",
    ):
        guard.check_action(
            "click",
            RiskLevel.RISKY,
        )