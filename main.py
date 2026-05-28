import argparse
import sys

from exceptions import LogFileNotFoundError, LogParserError
from models import LOG_LEVELS
from log_parser import LogParser
from reporter import Reporter

def _ask(prompt: str, valid: list = None, default: str = "") -> str:
    while True:
        raw = input(prompt).strip()
        if not raw and default:
            return default
        if valid is None or raw.upper() in [v.upper() for v in valid]:
            return raw
        print(f"  Please choose one of: {', '.join(valid)}")


def _print_entries(entries, limit: int = 50) -> None:
    shown = list(entries)[:limit]
    if not shown:
        print("  (no matching entries)")
        return
    for e in shown:
        print(f"  {e}")
    if len(list(entries)) > limit:  
        print(f"  … (showing first {limit} of {len(entries)} entries)")

def action_load(parser_state: dict) -> None:
    filepath = _ask("  Enter log file path: ")
    if not filepath:
        print("  No path given — keeping current file.")
        return
    try:
        lp = LogParser(filepath, lenient=True)
        lp.load()
        parser_state["parser"] = lp
        parser_state["filepath"] = filepath
        print(f"  ✓ Loaded {len(lp.entries)} entries.")
    except LogFileNotFoundError as exc:
        print(f"  ✗ {exc}")


def action_show_all(parser_state: dict) -> None:
    lp: LogParser = parser_state.get("parser")
    if not lp:
        print("  No file loaded. Use option 1 first.")
        return
    _print_entries(lp.entries)


def action_filter_level(parser_state: dict) -> None:
    lp: LogParser = parser_state.get("parser")
    if not lp:
        print("  No file loaded.")
        return
    level = _ask(f"  Level ({'/'.join(LOG_LEVELS)}): ", valid=LOG_LEVELS)
    entries = lp.filter_by_level_and_above(level)
    print(f"\n  Entries at {level} or above: {len(entries)}")
    _print_entries(entries)


def action_filter_keyword(parser_state: dict) -> None:
    lp: LogParser = parser_state.get("parser")
    if not lp:
        print("  No file loaded.")
        return
    kw = _ask("  Keyword to search: ")
    entries = lp.filter_by_keyword(kw)
    print(f"\n  Entries containing '{kw}': {len(entries)}")
    _print_entries(entries)


def action_filter_source(parser_state: dict) -> None:
    lp: LogParser = parser_state.get("parser")
    if not lp:
        print("  No file loaded.")
        return
    sources = lp.unique_sources()
    if sources:
        print(f"  Known sources: {', '.join(sorted(sources))}")
    src = _ask("  Source name (partial match ok): ")
    entries = lp.filter_by_source(src)
    print(f"\n  Entries from '{src}': {len(entries)}")
    _print_entries(entries)


def action_summary(parser_state: dict) -> None:
    lp: LogParser = parser_state.get("parser")
    if not lp:
        print("  No file loaded.")
        return
    reporter = Reporter(
        entries=lp.entries,
        level_counts=lp.level_counts(),
        source_counts=lp.source_counts(),
        source_file=parser_state.get("filepath", ""),
    )
    reporter.print_summary()


def action_errors(parser_state: dict) -> None:
    lp: LogParser = parser_state.get("parser")
    if not lp:
        print("  No file loaded.")
        return
    entries = lp.errors_and_above()
    print(f"\n  ERROR / CRITICAL entries: {len(entries)}")
    _print_entries(entries)


def action_save_json(parser_state: dict) -> None:
    lp: LogParser = parser_state.get("parser")
    if not lp:
        print("  No file loaded.")
        return
    reporter = Reporter(
        entries=lp.entries,
        level_counts=lp.level_counts(),
        source_counts=lp.source_counts(),
        source_file=parser_state.get("filepath", ""),
    )
    reporter.save_json()


def action_save_csv(parser_state: dict) -> None:
    lp: LogParser = parser_state.get("parser")
    if not lp:
        print("  No file loaded.")
        return
    reporter = Reporter(
        entries=lp.entries,
        level_counts=lp.level_counts(),
        source_counts=lp.source_counts(),
        source_file=parser_state.get("filepath", ""),
    )
    reporter.save_csv()


def action_filter_generator(parser_state: dict) -> None:
    lp: LogParser = parser_state.get("parser")
    if not lp:
        print("  No file loaded.")
        return
    level = _ask(f"  Level filter (leave blank to skip) [{'/'.join(LOG_LEVELS)}]: ") or None
    kw = _ask("  Keyword filter (leave blank to skip): ") or None
    gen = lp.iter_filtered(level=level, keyword=kw)
    count = 0
    for entry in gen:
        print(f"  {entry}")
        count += 1
        if count >= 50:
            print("  … (generator output truncated at 50 entries)")
            break
    print(f"\n  Streamed {count} entries via generator.")

MENU = [
    ("Load log file",                  action_load),
    ("Show all entries",               action_show_all),
    ("Filter by level (and above)",    action_filter_level),
    ("Filter by keyword",              action_filter_keyword),
    ("Filter by source",               action_filter_source),
    ("Show errors & criticals",        action_errors),
    ("Print summary",                  action_summary),
    ("Save JSON report",               action_save_json),
    ("Save CSV report",                action_save_csv),
    ("Stream entries (generator demo)", action_filter_generator),
    ("Quit",                           None),
]


def print_menu(parser_state: dict) -> None:
    loaded = parser_state.get("filepath")
    status = f"  File: {loaded}" if loaded else "  No file loaded"
    print(f"\n{'═' * 50}")
    print("  LOG PARSER")
    print(status)
    print(f"{'─' * 50}")
    for i, (label, _) in enumerate(MENU, start=1):
        print(f"  {i:2d}. {label}")
    print(f"{'═' * 50}")


def run_menu(parser_state: dict) -> None:
    while True:
        print_menu(parser_state)
        choice = _ask("  Choice: ")
        if not choice.isdigit():
            print("  Please enter a number.")
            continue
        idx = int(choice) - 1
        if idx < 0 or idx >= len(MENU):
            print("  Out of range.")
            continue
        label, action = MENU[idx]
        if action is None:
            print("  Goodbye!")
            sys.exit(0)
        try:
            action(parser_state)
        except LogParserError as exc:
            print(f"  ✗ Error: {exc}")
        except KeyboardInterrupt:
            print("\n  Interrupted.")

def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Log Parser — analyse log files and generate JSON/CSV reports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py\n"
            "  python main.py --file app.log\n"
            "  python main.py --file app.log --level ERROR --json\n"
        ),
    )
    ap.add_argument("--file", metavar="PATH", help="Log file to load on startup")
    ap.add_argument(
        "--level",
        metavar="LEVEL",
        choices=LOG_LEVELS,
        help="Filter: show this level and above",
    )
    ap.add_argument("--keyword", metavar="TEXT", help="Filter: entries containing TEXT")
    ap.add_argument("--json", action="store_true", help="Save JSON report and exit")
    ap.add_argument("--csv",  action="store_true", help="Save CSV report and exit")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Fail on unrecognised log lines (default: skip them)",
    )
    return ap


def run_cli(args: argparse.Namespace) -> None:
    lp = LogParser(args.file, lenient=not args.strict)
    lp.load()

    entries = lp.entries
    if args.level:
        entries = lp.filter_by_level_and_above(args.level)
    if args.keyword:
        keyword = args.keyword
        entries = [e for e in entries if keyword.lower() in e.message.lower()]

    reporter = Reporter(
        entries=entries,
        level_counts=lp.level_counts(),
        source_counts=lp.source_counts(),
        source_file=args.file,
    )
    reporter.print_summary()

    if args.json:
        reporter.save_json()
    if args.csv:
        reporter.save_csv()

def main() -> None:
    ap = build_arg_parser()
    args = ap.parse_args()

    parser_state: dict = {"parser": None, "filepath": None}

    if args.file:
        try:
            run_cli(args)
            if not (args.json or args.csv):
                lp = LogParser(args.file, lenient=not args.strict)
                lp.load()
                parser_state["parser"] = lp
                parser_state["filepath"] = args.file
                run_menu(parser_state)
        except LogParserError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        run_menu(parser_state)


if __name__ == "__main__":
    main()

