"""Custom exceptions for the application."""


class KEDBException(Exception):
    """Base exception for KEDB."""
    pass


class NotFoundError(KEDBException):
    """Resource not found."""
    pass


class ValidationError(KEDBException):
    """Validation failed."""
    pass


class ConflictError(KEDBException):
    """Resource conflict (e.g., duplicate)."""
    pass


class WorkflowError(KEDBException):
    """Invalid workflow state transition."""
    pass


class PermissionError(KEDBException):
    """Permission denied."""
    pass
