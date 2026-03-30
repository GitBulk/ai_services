import uuid
from dataclasses import dataclass


def generate_id():
    return uuid.uuid4().hex[:16]


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_id: str | None
    name: str
    start_time: int
    end_time: int | None = None

    def finish(self, end_time: int):
        self.end_time = end_time
