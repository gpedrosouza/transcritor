"""Base exceptions for Transcritor Musical."""


class TranscritorError(Exception):
    """Base class for all errors raised by Transcritor packages."""


class SchemaVersionError(TranscritorError):
    """Raised when a document has an unsupported Score IR schema version."""

    def __init__(self, message: str, found: str) -> None:
        super().__init__(message)
        self.found = found


class StageOutputError(TranscritorError):
    """Raised when a stage returns a document that violates the Score IR contract."""

    def __init__(self, message: str, stage: str) -> None:
        super().__init__(message)
        self.stage = stage
