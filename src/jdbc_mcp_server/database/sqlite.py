"""
SQLite database adapter implementation.

SQLite is a file-based database with no network connectivity, making it
ideal for testing and local development.
"""

import sqlite3
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple
import logging

from jdbc_mcp_server.database.base import DatabaseAdapter
from jdbc_mcp_server.errors import (
    ConnectionError,
    QueryError,
    ValidationError,
    NotFoundError,
    map_driver_error,
)
from jdbc_mcp_server.utils import serialize_row

logger = logging.getLogger(__name__)


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter using the built-in sqlite3 module."""

    def __init__(self, connection_string: str, read_only: bool = True):
        """
        Initialize SQLite adapter.

        Args:
            connection_string: SQLite connection string (e.g., "sqlite:////path/to/file.db")
            read_only: Whether to enforce read-only mode
        """
        super().__init__(connection_string, read_only)

        # Extract file path from connection string
        # Format: sqlite:////absolute/path or sqlite:///:memory:
        if connection_string.startswith("sqlite:///"):
            self.db_path = connection_string[10:]  # Remove "sqlite:///"
        else:
            raise ValueError(f"Invalid SQLite connection string: {connection_string}")

        logger.info(f"SQLite adapter initialized for: {self.db_path}")

    async def initialize(self) -> None:
        """Initialize SQLite database (no connection pool needed)."""
        logger.info(f"Initializing SQLite adapter for {self.db_path}")
        # SQLite doesn't use connection pooling - connections are created per-request
        pass

    async def close(self) -> None:
        """Close SQLite adapter (no persistent connections to close)."""
        logger.info(f"Closing SQLite adapter for {self.db_path}")
        pass

    @asynccontextmanager
    async def get_connection(self):
        """
        Get SQLite database connection.

        Yields:
            sqlite3.Connection object
        """
        conn = None
        try:
            # check_same_thread=False allows usage from async context
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row  # Allow dict-like access to rows
            yield conn
        except sqlite3.Error as e:
            raise map_driver_error(e, self.driver_type)
        finally:
            if conn:
                conn.close()

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute SELECT query against SQLite database."""
        # Validate query safety
        self._validate_query_safety(query)

        # Sanitize parameters
        parameters = self._sanitize_parameters(parameters)

        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()

                # Execute query with parameters
                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)

                # Fetch results
                rows = cursor.fetchall()

                # Convert to list of dicts
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                result = [serialize_row(tuple(row), columns) for row in rows]

                logger.info(f"SQLite query returned {len(result)} rows")
                return result

        except sqlite3.Error as e:
            logger.error(f"SQLite query error: {e}")
            raise map_driver_error(e, self.driver_type)

    def quote_identifier(self, identifier: str) -> str:
        """
        Quote an identifier using SQLite rules (double quotes).
        """
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValidationError("Identifier cannot be empty")

        sanitized = identifier.replace('"', '""')
        return f'"{sanitized}"'

    async def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """List all tables in the SQLite database."""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
                tables = [row[0] for row in cursor.fetchall()]
                logger.info(f"Found {len(tables)} tables in SQLite database")
                return tables

        except sqlite3.Error as e:
            logger.error(f"Error listing tables: {e}")
            raise map_driver_error(e, self.driver_type)

    async def get_table_schema(
        self,
        table_name: str,
        schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get column information for a SQLite table."""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get column info using PRAGMA
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()

                if not columns_info:
                    raise NotFoundError(
                        f"Table '{table_name}' not found",
                        "table",
                        table_name
                    )

                # Convert to standardized format
                schema = []
                for col in columns_info:
                    schema.append({
                        'name': col[1],  # column name
                        'type': col[2],  # data type
                        'nullable': not bool(col[3]),  # NOT NULL flag (inverted)
                        'primary_key': bool(col[5]),  # PK flag
                        'default': col[4]  # default value
                    })

                logger.info(f"Retrieved schema for table '{table_name}' with {len(schema)} columns")
                return schema

        except sqlite3.Error as e:
            logger.error(f"Error getting table schema: {e}")
            raise map_driver_error(e, self.driver_type)

    async def get_schemas(self) -> List[str]:
        """SQLite has no schemas - return empty list."""
        return []

    async def test_connection(self) -> Dict[str, Any]:
        """Test SQLite connection and get database info."""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get SQLite version
                cursor.execute("SELECT sqlite_version()")
                version = cursor.fetchone()[0]

                # Count tables
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]

                return {
                    'connected': True,
                    'database_type': 'SQLite',
                    'version': version,
                    'database_name': self.db_path,
                    'table_count': table_count
                }

        except sqlite3.Error as e:
            logger.error(f"Connection test failed: {e}")
            return {
                'connected': False,
                'database_type': 'SQLite',
                'error': str(e)
            }

    @property
    def driver_type(self) -> str:
        """Get driver type identifier."""
        return "sqlite"

    @property
    def paramstyle(self) -> str:
        """Get parameter style (SQLite uses qmark: ?)."""
        return "qmark"
