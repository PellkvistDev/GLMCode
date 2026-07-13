"""Structured error types for GLM Code.

Errors are categorized by severity (error, warning, info) and include
user-friendly messages with technical details.
"""

from __future__ import annotations

from enum import Enum


class ErrorSeverity(Enum):
    """Severity level of an error."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ToolError(Exception):
    """Base error for tool failures. Converted to user-visible error messages."""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message)
        self.message = message
        self.severity = severity


class ApiError(Exception):
    """Error from the API (429, 5xx, etc.)."""
    def __init__(self, status: int, message: str):
        super().__init__(f"API error {status}: {message}")
        self.status = status
        self.message = message
        self.severity = ErrorSeverity.ERROR


class Cancelled(Exception):
    """Raised when the user cancels a streaming request."""
    pass


class ValidationError(Exception):
    """Error for invalid user input or configuration."""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message)
        self.message = message
        self.severity = severity


class PermissionDeniedError(Exception):
    """Raised when a tool call is denied by permissions."""
    def __init__(self, tool_name: str, reason: str = ""):
        message = f"Permission denied for {tool_name}"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.tool_name = tool_name
        self.reason = reason
        self.severity = ErrorSeverity.ERROR


class SessionNotFoundError(Exception):
    """Raised when trying to load a non-existent session."""
    def __init__(self, session_id: str):
        super().__init__(f"Session not found: {session_id}")
        self.session_id = session_id
        self.severity = ErrorSeverity.ERROR


class ConfigurationError(Exception):
    """Error for configuration issues."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
        self.severity = ErrorSeverity.ERROR
