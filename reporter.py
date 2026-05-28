import csv
import json
import os
from datetime import datetime
from typing import List

from decorators import timed
from exceptions import ReportGenerationError
from models import LogEntry


_REPORTS_DIR = "reports"


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _timestamp_str() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _entry_to_dict(entry: LogEntry) -> dict:
    return {
        "line_number": entry.line_number,
        "timestamp": entry.formatted_timestamp(),
        "level": entry.level,
        "source": entry.source or "",
        "message": entry.message,
        "extra": entry.extra,
    }


class Reporter:

    def __init__(
        self,
        entries: List[LogEntry],
        level_counts: dict,
        source_counts: dict,
        source_file: str = "",
    ):
        self.entries = entries
        self.level_counts = level_counts
        self.source_counts = source_counts
        self.source_file = source_file


    @timed
    def save_json(self, filepath: str = "") -> str:

        if not filepath:
            _ensure_dir(_REPORTS_DIR)
            filepath = os.path.join(_REPORTS_DIR, f"report_{_timestamp_str()}.json")

        payload = {
            "metadata": {
                "source_file": self.source_file,
                "generated_at": datetime.now().isoformat(),
                "total_entries": len(self.entries),
            },
            "summary": {
                "level_counts": self.level_counts,
                "source_counts": self.source_counts,
            },
            "entries": [_entry_to_dict(e) for e in self.entries],
        }

        try:
            with open(filepath, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            raise ReportGenerationError(str(exc)) from exc

        print(f"  JSON report saved → {filepath}")
        return filepath
    @timed
    def save_csv(self, filepath: str = "") -> str:

        if not filepath:
            _ensure_dir(_REPORTS_DIR)
            filepath = os.path.join(_REPORTS_DIR, f"entries_{_timestamp_str()}.csv")

        fieldnames = ["line_number", "timestamp", "level", "source", "message"]

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(_entry_to_dict(e) for e in self.entries)
        except OSError as exc:
            raise ReportGenerationError(str(exc)) from exc

        print(f"  CSV report saved  → {filepath}")
        return filepath

    def print_summary(self) -> None:
        total = len(self.entries)
        print(f"\n{'─' * 50}")
        print(f"  Total entries : {total}")
        print(f"  Level breakdown:")
        for level, count in sorted(self.level_counts.items()):
            bar = "█" * min(count, 30)
            print(f"    {level:10s} {count:5d}  {bar}")
        if self.source_counts:
            print(f"  Top sources:")
            sorted_sources = sorted(
                self.source_counts.items(),
                key=lambda kv: (-kv[1], kv[0]),
            )
            for src, cnt in sorted_sources[:10]:
                print(f"    {src:20s} {cnt:5d}")
        print(f"{'─' * 50}\n")