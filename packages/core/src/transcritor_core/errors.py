"""Base exceptions for Transcritor Musical."""


class TranscritorError(Exception):
    """Base class for all errors raised by Transcritor packages."""


class SchemaVersionError(TranscritorError):
    """Raised when a document has an unsupported Score IR schema version."""

    def __init__(self, message: str, found: str) -> None:
        super().__init__(message)
        self.found = found
