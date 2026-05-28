import re
import os
from datetime import datetime
from typing import Iterator, List, Optional

from decorators import timed
from exceptions import InvalidLogFormatError, LogFileNotFoundError
from models import LogEntry


_RE_STANDARD = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})"   # timestamp
    r"\s+(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)"       # level
    r"(?:\s+\[(?P<source>[^\]]+)\])?"                        # optional [source]
    r"\s+(?P<message>.+)$",                                  # message
    re.IGNORECASE,
)

_RE_SIMPLE = re.compile(
    r"^(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)[:\s]\s*(?P<message>.+)$",
    re.IGNORECASE,
)

_RE_KV = re.compile(r"(\w+)=([^\s,]+)")

_TS_FORMATS = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]


def _parse_timestamp(raw: str) -> datetime:
    for fmt in _TS_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognised timestamp: {raw!r}")


def _extract_kv(message: str) -> dict:
    return {k: v for k, v in _RE_KV.findall(message)}


def parse_line(raw: str, line_number: Optional[int] = None) -> LogEntry:

    line = raw.strip()
    if not line:
        raise InvalidLogFormatError(line, line_number)

    m = _RE_STANDARD.match(line)
    if m:
        ts = _parse_timestamp(m.group("ts").replace("T", " "))
        return LogEntry(
            timestamp=ts,
            level=m.group("level").upper(),
            source=m.group("source"),
            message=m.group("message"),
            raw=raw,
            line_number=line_number,
            extra=_extract_kv(m.group("message")),
        )

    m = _RE_SIMPLE.match(line)
    if m:
        return LogEntry(
            timestamp=datetime.now(),
            level=m.group("level").upper(),
            source=None,
            message=m.group("message"),
            raw=raw,
            line_number=line_number,
            extra=_extract_kv(m.group("message")),
        )

    raise InvalidLogFormatError(line, line_number)


def iter_entries(filepath: str, lenient: bool = False) -> Iterator[LogEntry]:

    if not os.path.isfile(filepath):
        raise LogFileNotFoundError(filepath)

    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        for lineno, raw in enumerate(fh, start=1):
            try:
                yield parse_line(raw, line_number=lineno)
            except InvalidLogFormatError:
                if not lenient:
                    raise

class LogParser:

    def __init__(self, filepath: str, lenient: bool = True):
        self.filepath = filepath
        self.lenient = lenient
        self._entries: List[LogEntry] = []

    @timed
    def load(self) -> "LogParser":
        self._entries = list(iter_entries(self.filepath, lenient=self.lenient))
        print(f"  Loaded {len(self._entries)} entries from '{self.filepath}'")
        return self

    def filter_by_level(self, level: str) -> List[LogEntry]:
        lvl = level.upper()
        return [e for e in self._entries if e.level == lvl]

    def filter_by_level_and_above(self, level: str) -> List[LogEntry]:
        from models import LEVEL_SEVERITY

        threshold = LEVEL_SEVERITY.get(level.upper(), 0)
        return [e for e in self._entries if e.severity >= threshold]

    def filter_by_source(self, source: str) -> List[LogEntry]:
        return [e for e in self._entries if e.source and source.lower() in e.source.lower()]

    def filter_by_keyword(self, keyword: str) -> List[LogEntry]:
        kw = keyword.lower()
        return [e for e in self._entries if kw in e.message.lower()]

    def errors_and_above(self) -> List[LogEntry]:
        return [e for e in self._entries if e.is_error_or_above()]

    def iter_filtered(self, level: Optional[str] = None, keyword: Optional[str] = None):

        for entry in self._entries:
            if level and entry.level != level.upper():
                continue
            if keyword and keyword.lower() not in entry.message.lower():
                continue
            yield entry

    def level_counts(self) -> dict:
        counts: dict = {}
        for entry in self._entries:
            counts[entry.level] = counts.get(entry.level, 0) + 1
        return counts

    def source_counts(self) -> dict:
        counts: dict = {}
        for entry in self._entries:
            key = entry.source or "<unknown>"
            counts[key] = counts.get(key, 0) + 1
        return counts

    def unique_sources(self) -> set:
        return {e.source for e in self._entries if e.source}

    @property
    def entries(self) -> List[LogEntry]:
        return self._entries