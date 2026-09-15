from urllib.parse import urlparse

from automation.models import RiskLevel


class PolicyViolation(Exception):
    pass


class PolicyGuard:
    def __init__(self):
        self.allowed_hosts = {
            "127.0.0.1:8000",
            "localhost:8000",
        }

        self.allowed_actions = {
            "navigate",
            "fill",
            "click",
            "extract",
        }

    def check_url(self, url: str):
        parsed = urlparse(url)

        host = parsed.netloc

        if host not in self.allowed_hosts:
            raise PolicyViolation(
                f"Domain not allowed: {host}"
            )

    def check_action(
        self,
        action: str,
        risk: RiskLevel,
    ):
        if action not in self.allowed_actions:
            raise PolicyViolation(
                f"Action not allowed: {action}"
            )

        if risk in {
            RiskLevel.RISKY,
            RiskLevel.IRREVERSIBLE,
        }:
            raise PolicyViolation(
                f"Human approval required for risk level: {risk.value}"
            )