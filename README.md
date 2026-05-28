# Project PPY - Log Parser and Reporter

`Project PPY` is a Python console application for parsing log files, filtering records, and generating reports in JSON/CSV formats.

The project supports:
- two log input formats (standard and simplified),
- interactive menu mode,
- command-line (CLI) mode with arguments,
- summary statistics by level and source,
- exporting reports to the `reports/` directory.

---

## Features

- Parse log lines into structured `LogEntry` objects
- Filter entries by:
  - level and above (`ERROR` includes `ERROR` + `CRITICAL`)
  - keyword
  - source (partial match)
- Show only error-level incidents (`ERROR` and `CRITICAL`)
- Stream filtered entries with a generator
- Print concise text summary with simple bar visualization
- Save reports:
  - JSON (`report_YYYYMMDD_HHMMSS.json`)
  - CSV (`entries_YYYYMMDD_HHMMSS.csv`)
- Strict vs lenient parsing modes

---

## Project Structure

- `main.py` - app entry point, CLI argument handling, interactive menu
- `log_parser.py` - log parsing logic, regexes, parser class, filtering APIs
- `reporter.py` - summary printing and JSON/CSV export
- `models.py` - `LogEntry` dataclass, severity mapping, helpers
- `exceptions.py` - domain-specific exceptions
- `decorators.py` - utility decorators (`timed`, etc.)
- `splunkconnector.py` - standalone experimental Splunk connection snippet

---

## Requirements

- Python 3.9+ (recommended)
- No mandatory third-party dependencies for core parser/reporter workflow

Optional (only for `splunkconnector.py`):
- `splunk-sdk` / `splunklib`

---

## Quick Start

From the project folder:

```bash
python3 main.py
```

This starts the interactive menu.

---

## Interactive Menu Mode

When started without `--file`, the app opens a console menu.

Main actions:
1. Load log file
2. Show all entries
3. Filter by level (and above)
4. Filter by keyword
5. Filter by source
6. Show errors & criticals
7. Print summary
8. Save JSON report
9. Save CSV report
10. Stream entries (generator demo)
11. Quit

---

## CLI Mode

You can load a file immediately using command-line arguments.

### Basic

```bash
python3 main.py --file app.log
```

### Filter by level and show summary

```bash
python3 main.py --file app.log --level ERROR
```

### Filter by keyword

```bash
python3 main.py --file app.log --keyword timeout
```

### Export reports and exit

```bash
python3 main.py --file app.log --json --csv
```

### Strict parsing mode

```bash
python3 main.py --file app.log --strict
```

`--strict` means any invalid line causes failure.  
Without `--strict`, invalid lines are skipped (lenient mode).

---

## Supported Log Formats

### 1) Standard format

```text
YYYY-MM-DD HH:MM:SS LEVEL [source] message
```

or

```text
YYYY-MM-DDTHH:MM:SS LEVEL [source] message
```

Examples:

```text
2026-05-28 12:00:00 INFO [auth] user login success user_id=42
2026-05-28T12:01:03 ERROR [db] query timeout duration_ms=5000
```

### 2) Simplified format

```text
LEVEL: message
```

or

```text
LEVEL message
```

Example:

```text
WARNING: disk usage high percent=91
```

Notes:
- Levels are case-insensitive while parsing, then normalized to uppercase.
- `key=value` pairs inside message are extracted into `entry.extra`.
- Simplified format uses current timestamp (`datetime.now()`).

---

## Output and Reports

Generated reports are saved to:

```text
reports/
```

### JSON report includes
- metadata (`source_file`, generation time, total entries)
- summary (`level_counts`, `source_counts`)
- full list of parsed entries

### CSV report includes columns
- `line_number`
- `timestamp`
- `level`
- `source`
- `message`

---

## Error Handling

Custom exceptions:
- `LogParserError` - base class
- `InvalidLogFormatError` - bad line format
- `LogFileNotFoundError` - missing input file
- `ReportGenerationError` - write/export failure

In menu mode, parser errors are shown and app continues working.  
In CLI mode with `--file`, fatal parser errors return exit code `1`.

---

## Developer Notes

- Parsing pipeline is split into:
  - `parse_line(...)` for per-line decoding
  - `iter_entries(...)` for file iteration and strict/lenient behavior
  - `LogParser` methods for loaded-data filtering and aggregation
- `@timed` decorator prints runtime for selected operations (`load`, `save_json`, `save_csv`).

---

## Splunk Connector Note

`splunkconnector.py` is not part of the main parser flow and appears to be a separate integration experiment.

If you plan to use it:
- install Splunk SDK dependency,
- move credentials/URLs to environment variables,
- never commit real credentials into source control.

---

## Typical Workflow

1. Start app:
   ```bash
   python3 main.py
   ```
2. Load a log file in menu option `1`
3. Inspect entries and apply filters
4. Print summary
5. Export JSON/CSV report

For automated usage:

```bash
python3 main.py --file app.log --level WARNING --keyword auth --json
```

---

## License

No explicit license file is currently included in this folder.  
Add a `LICENSE` file if this project will be distributed.

