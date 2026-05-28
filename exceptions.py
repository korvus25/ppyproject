class LogParserError(Exception):
    pass

class InvalidLogFormatError(LogParserError):

    def __init__(self, line: str, line_number: int = None):
        location = f" (line {line_number})" if line_number is not None else ""
        super().__init__(f"Invalid log format{location}: {line!r}")
        self.line = line
        self.line_number = line_number


class LogFileNotFoundError(LogParserError):

    def __init__(self, filepath: str):
        super().__init__(f"Log file not found: '{filepath}'")
        self.filepath = filepath


class ReportGenerationError(LogParserError):

    def __init__(self, reason: str):
        super().__init__(f"Failed to generate report: {reason}")