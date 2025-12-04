"""
Exception hierarchy for database operations.

Provides structured error handling with user-friendly messages for MCP responses.
"""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCategory(Enum):
    """Categories of database errors for classification."""

    CONNECTION = "connection_error"
    AUTHENTICATION = "authentication_error"
    QUERY = "query_error"
    VALIDATION = "validation_error"
    SECURITY = "security_error"
    TIMEOUT = "timeout_error"
    DRIVER = "driver_specific_error"
    NOT_FOUND = "not_found_error"


class DatabaseError(Exception):
    """Base exception for all database operations."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        recoverable: bool = False,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize database error.

        Args:
            message: Human-readable error message
            category: Error category for classification
            recoverable: Whether the error can be recovered from
            original_error: The original exception that caused this error
        """
        self.message = message
        self.category = category
        self.recoverable = recoverable
        self.original_error = original_error
        super().__init__(message)

    def to_mcp_error(self) -> Dict[str, Any]:
        """
        Convert error to MCP-friendly format for responses.

        Returns:
            Dictionary with error details suitable for JSON serialization
        """
        return {
            "error": self.message,
            "category": self.category.value,
            "recoverable": self.recoverable,
            "details": str(self.original_error) if self.original_error else None
        }


class ConnectionError(DatabaseError):
    """Error connecting to database."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            ErrorCategory.CONNECTION,
            recoverable=True,  # Connection errors are often recoverable
            original_error=original_error
        )


class AuthenticationError(DatabaseError):
    """Error authenticating to database."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            ErrorCategory.AUTHENTICATION,
            recoverable=False,  # Auth errors require credential fixes
            original_error=original_error
        )


class QueryError(DatabaseError):
    """Error executing database query."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            ErrorCategory.QUERY,
            recoverable=False,  # Query errors usually mean bad SQL
            original_error=original_error
        )


class ValidationError(DatabaseError):
    """Error validating input parameters."""

    def __init__(self, message: str):
        super().__init__(
            message,
            ErrorCategory.VALIDATION,
            recoverable=False,  # Validation errors require input fixes
            original_error=None
        )


class SecurityError(DatabaseError):
    """Security-related error (SQL injection attempt, etc.)."""

    def __init__(self, message: str):
        super().__init__(
            message,
            ErrorCategory.SECURITY,
            recoverable=False,  # Security errors should not be recovered from
            original_error=None
        )


class TimeoutError(DatabaseError):
    """Query execution timeout."""

    def __init__(self, message: str, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(
            message,
            ErrorCategory.TIMEOUT,
            recoverable=True,  # Can retry with different query
            original_error=None
        )


class NotFoundError(DatabaseError):
    """Resource not found (table, database, etc.)."""

    def __init__(self, message: str, resource_type: str, resource_name: str):
        self.resource_type = resource_type
        self.resource_name = resource_name
        super().__init__(
            message,
            ErrorCategory.NOT_FOUND,
            recoverable=False,
            original_error=None
        )


def map_driver_error(error: Exception, driver_type: str) -> DatabaseError:
    """
    Map driver-specific errors to user-friendly DatabaseError instances.

    Args:
        error: The original driver exception
        driver_type: Type of database driver (postgresql, mysql, sqlite, db2)

    Returns:
        Appropriate DatabaseError subclass with user-friendly message
    """
    error_str = str(error).lower()

    # PostgreSQL errors
    if driver_type == "postgresql":
        if "connection refused" in error_str:
            return ConnectionError(
                "Cannot connect to PostgreSQL server. Check if the server is running "
                "and that the connection details are correct.",
                error
            )
        if "authentication failed" in error_str or "password authentication failed" in error_str:
            return AuthenticationError(
                "Invalid username or password for PostgreSQL database.",
                error
            )
        if "does not exist" in error_str:
            if "database" in error_str:
                return NotFoundError(
                    "PostgreSQL database does not exist.", "database", ""
                )
            return NotFoundError(
                "Table or column does not exist in the database.", "table/column", ""
            )

    # MySQL errors
    elif driver_type == "mysql":
        if "access denied" in error_str:
            return AuthenticationError(
                "Access denied for MySQL user. Check username and password.",
                error
            )
        if "unknown database" in error_str:
            return NotFoundError(
                "MySQL database does not exist.", "database", ""
            )
        if "can't connect" in error_str or "connection refused" in error_str:
            return ConnectionError(
                "Cannot connect to MySQL server. Check if the server is running "
                "and connection details are correct.",
                error
            )

    # SQLite errors
    elif driver_type == "sqlite":
        if "no such table" in error_str:
            return NotFoundError(
                "Table does not exist in SQLite database.", "table", ""
            )
        if "database is locked" in error_str:
            return ConnectionError(
                "SQLite database is locked by another process. Try again in a moment.",
                error
            )
        if "unable to open database file" in error_str:
            return ConnectionError(
                "Cannot open SQLite database file. Check file path and permissions.",
                error
            )

    # DB2 errors
    elif driver_type == "db2":
        if "sql0204n" in error_str:
            return NotFoundError(
                "Table or view not found in DB2 database.", "table/view", ""
            )
        if "sql30081n" in error_str:
            return ConnectionError(
                "Cannot connect to DB2 server. Check network connectivity "
                "and connection details.",
                error
            )
        if "sql30082n" in error_str:
            return AuthenticationError(
                "DB2 authentication failed. Check username and password.",
                error
            )

    # Generic fallback
    return QueryError(f"Database error: {str(error)}", error)
