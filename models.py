from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

LEVEL_SEVERITY = {level: i for i, level in enumerate(LOG_LEVELS)}


@dataclass
class LogEntry:

    timestamp: datetime
    level: str
    message: str
    raw: str
    source: Optional[str] = None
    line_number: Optional[int] = None

    # Extra key=value pairs captured from structured logs
    extra: dict = field(default_factory=dict)

    @property
    def severity(self) -> int:
        return LEVEL_SEVERITY.get(self.level, -1)

    def is_error_or_above(self) -> bool:
        return self.severity >= LEVEL_SEVERITY["ERROR"]

    def formatted_timestamp(self) -> str:

        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self) -> str:
        source_part = f"[{self.source}] " if self.source else ""
        return f"{self.formatted_timestamp()} {self.level:8s} {source_part}{self.message}"