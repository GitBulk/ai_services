from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TimePayload:
    epoch_ms: int
    rfc3339: str
    current: datetime  # source of truth
