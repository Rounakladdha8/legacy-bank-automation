from enum import Enum
from typing import List

from pydantic import BaseModel


class RiskLevel(str, Enum):
    SAFE = "safe"
    REVERSIBLE = "reversible"
    RISKY = "risky"
    IRREVERSIBLE = "irreversible"


class LocatorSpec(BaseModel):
    strategy: str
    value: str


class RetryPolicy(BaseModel):
    max_attempts: int = 1
    wait_seconds: float = 0


class Checkpoint(BaseModel):
    type: str
    expected: str


class InputSpec(BaseModel):
    name: str
    type: str
    required: bool = True
    sensitive: bool = False


class OutputSpec(BaseModel):
    name: str
    type: str


class Step(BaseModel):
    step_id: str
    action: str
    target: LocatorSpec | None = None
    value: str | None = None

    retry: RetryPolicy = RetryPolicy()
    checkpoint: Checkpoint | None = None
    risk: RiskLevel = RiskLevel.SAFE


class BusinessOutcome(BaseModel):
    code: str
    description: str


class CapabilityArtifact(BaseModel):
    schema_version: str
    capability_id: str
    name: str
    version: str

    inputs: List[InputSpec]
    outputs: List[OutputSpec]
    steps: List[Step]

    success_condition: Checkpoint
    business_outcomes: List[BusinessOutcome] = []

class ReplayStatus(str, Enum):
    SUCCESS = "success"
    BUSINESS_OUTCOME = "business_outcome"
    RECOVERABLE_CONDITION = "recoverable_condition"
    HARD_FAILURE = "hard_failure"


class ReplayResult(BaseModel):
    status: ReplayStatus
    code: str | None = None
    outputs: dict[str, str] = {}

    step_id: str | None = None
    expected: str | None = None
    observed: str | None = None
    message: str | None = None    