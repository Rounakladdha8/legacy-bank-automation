from enum import Enum

from pydantic import BaseModel


class DiscoveryActionType(str, Enum):
    FILL = "fill"
    CLICK = "click"
    EXTRACT = "extract"
    FINISH = "finish"
    ESCALATE = "escalate"


class DiscoveryAction(BaseModel):
    action: DiscoveryActionType

    target: str | None = None
    value: str | None = None

    output_name: str | None = None
    output_value: str | None = None

    reason: str