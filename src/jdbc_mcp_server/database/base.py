"""
Abstract base class for database adapters.

Defines the interface that all database adapters must implement to provide
a unified way to interact with different database types.
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple
import sqlparse

from jdbc_mcp_server.errors import SecurityError, ValidationError


class DatabaseAdapter(ABC):
    """
    Abstract base class for database adapters.

    All database adapters must implement this interface to ensure consistent
    behavior across different database types.
    """

    def __init__(self, connection_string: str, read_only: bool = True):
        """
        Initialize database adapter.

        Args:
            connection_string: Database connection string
            read_only: Whether to enforce read-only mode (default: True)
        """
        self.connection_string = connection_string
        self.read_only = read_only
        self._pool = None

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize database connection pool or resources.

        This is called once at server startup.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close database connections and cleanup resources.

        This is called at server shutdown.
        """
        pass

    @abstractmethod
    @asynccontextmanager
    async def get_connection(self):
        """
        Context manager for acquiring and releasing database connections.

        Yields:
            Database connection object

        Example:
            async with adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        pass

    @abstractmethod
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute SELECT query with parameterized inputs.

        Args:
            query: SQL SELECT query
            parameters: Tuple of parameter values for placeholders

        Returns:
            List of rows as dictionaries with column names as keys

        Raises:
            SecurityError: If query violates security policies
            QueryError: If query execution fails
        """
        pass

    @abstractmethod
    async def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        List all tables in the database or specific schema.

        Args:
            schema: Optional schema name (None for default schema)

        Returns:
            List of table names
        """
        pass

    @abstractmethod
    async def get_table_schema(
        self,
        table_name: str,
        schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get column information for a table.

        Args:
            table_name: Name of the table
            schema: Optional schema name

        Returns:
            List of column metadata dictionaries with keys:
                - name: column name
                - type: data type
                - nullable: bool
                - primary_key: bool (if available)
                - default: default value (if available)
        """
        pass

    @abstractmethod
    async def get_schemas(self) -> List[str]:
        """
        List all schemas/databases.

        Returns:
            List of schema names (empty for SQLite which has no schemas)
        """
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test database connectivity and get server information.

        Returns:
            Dictionary with connection status and metadata:
                - connected: bool
                - database_type: str
                - version: str
                - database_name: str
        """
        pass

    @property
    @abstractmethod
    def driver_type(self) -> str:
        """
        Get the database driver type identifier.

        Returns:
            One of: 'postgresql', 'mysql', 'sqlite', 'db2'
        """
        pass

    @property
    @abstractmethod
    def paramstyle(self) -> str:
        """
        Get the parameter style for this database.

        Returns:
            One of: 'qmark', 'numeric', 'named', 'format', 'pyformat'
            (from DB-API 2.0 specification)
        """
        pass

    def _validate_query_safety(self, query: str) -> None:
        """
        Validate query doesn't contain dangerous operations.

        Args:
            query: SQL query to validate

        Raises:
            SecurityError: If query contains dangerous operations
        """
        if not query or not query.strip():
            raise ValidationError("Query cannot be empty")

        # Parse the query
        try:
            parsed = sqlparse.parse(query)
        except Exception as e:
            raise ValidationError(f"Invalid SQL syntax: {e}")

        if not parsed:
            raise ValidationError("Could not parse SQL query")

        # Check for multiple statements
        if len(parsed) > 1:
            raise SecurityError(
                "Multiple SQL statements are not allowed. "
                "Execute one query at a time."
            )

        # Check for comments (can hide malicious code)
        if '--' in query or '/*' in query:
            raise SecurityError(
                "SQL comments are not allowed in queries for security reasons."
            )

        # If read-only mode, ensure only SELECT statements
        if self.read_only:
            dangerous_keywords = [
                'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
                'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
            ]

            query_upper = query.upper()
            for keyword in dangerous_keywords:
                # Check for keyword as a whole word (not part of another word)
                if f' {keyword} ' in f' {query_upper} ':
                    raise SecurityError(
                        f"Query contains '{keyword}' but server is in read-only mode. "
                        f"Only SELECT queries are allowed."
                    )

            # Get statement type
            stmt = parsed[0]
            stmt_type = stmt.get_type()
            if stmt_type and stmt_type != 'SELECT' and stmt_type != 'UNKNOWN':
                raise SecurityError(
                    f"Only SELECT queries are allowed in read-only mode. "
                    f"Got: {stmt_type}"
                )

    def _sanitize_parameter(self, value: Any) -> Any:
        """
        Sanitize input parameter to prevent injection attacks.

        Args:
            value: Parameter value to sanitize

        Returns:
            Sanitized value

        Raises:
            ValidationError: If value is invalid
        """
        if value is None:
            return None

        if isinstance(value, str):
            # Remove null bytes
            value = value.replace('\x00', '')

            # Limit length to prevent DoS
            if len(value) > 10000:
                raise ValidationError(
                    "Parameter value too long (max 10000 characters)"
                )

        return value

    def _sanitize_parameters(self, parameters: Optional[Tuple]) -> Optional[Tuple]:
        """
        Sanitize all parameters in a tuple.

        Args:
            parameters: Tuple of parameter values

        Returns:
            Tuple of sanitized values
        """
        if not parameters:
            return None

        return tuple(self._sanitize_parameter(p) for p in parameters)
