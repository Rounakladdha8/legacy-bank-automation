import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EvidenceLogger:
    def __init__(self, run_id: str):
        self.run_id = run_id

        Path("evidence").mkdir(
            parents=True,
            exist_ok=True,
        )

        self.log_path = Path(
            f"evidence/{run_id}.jsonl"
        )

    def _redact_value(
        self,
        key: str,
        value: Any,
    ) -> Any:
        sensitive_keys = {
            "member_id",
            "password",
            "token",
            "api_key",
            "secret",
        }

        if key in sensitive_keys:
            return "[REDACTED]"

        return value

    def _sanitize(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            key: self._redact_value(
                key,
                value,
            )
            for key, value in data.items()
        }

    def log(
        self,
        event: str,
        **data: Any,
    ):
        record = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "run_id": self.run_id,
            "event": event,
            **self._sanitize(data),
        }

        with self.log_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(record)
                + "\n"
            )