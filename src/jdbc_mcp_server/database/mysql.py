"""
MySQL database adapter implementation.

Uses mysql-connector-python with connection pooling for efficient connection management.
"""

import mysql.connector
from mysql.connector import pooling, Error as MySQLError
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


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter using mysql-connector-python with connection pooling."""

    def __init__(self, connection_string: str, read_only: bool = True, pool_size: int = 5):
        """
        Initialize MySQL adapter.

        Args:
            connection_string: MySQL connection string
                              (e.g., "mysql://user:pass@localhost:3306/database")
            read_only: Whether to enforce read-only mode
            pool_size: Number of connections in the pool
        """
        super().__init__(connection_string, read_only)
        self.pool_size = pool_size
        self._pool: Optional[pooling.MySQLConnectionPool] = None
        self._connection_config = self._parse_connection_string(connection_string)
        logger.info(f"MySQL adapter initialized with pool size: {pool_size}")

    def _parse_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """
        Parse MySQL connection string into connection configuration.

        Args:
            connection_string: MySQL connection string (mysql://user:pass@host:port/database)

        Returns:
            Dictionary of connection parameters
        """
        # Format: mysql://username:password@hostname:port/database
        if not connection_string.startswith("mysql://"):
            raise ValueError(f"Invalid MySQL connection string: {connection_string}")

        # Remove mysql:// prefix
        conn_str = connection_string[8:]

        # Split credentials and host/db
        if "@" in conn_str:
            credentials, host_db = conn_str.split("@", 1)
            if ":" in credentials:
                user, password = credentials.split(":", 1)
            else:
                user = credentials
                password = ""
        else:
            raise ValueError("MySQL connection string must include credentials")

        # Split host/port and database
        if "/" in host_db:
            host_port, database = host_db.split("/", 1)
        else:
            raise ValueError("MySQL connection string must include database name")

        # Split host and port
        if ":" in host_port:
            host, port = host_port.split(":", 1)
            port = int(port)
        else:
            host = host_port
            port = 3306

        return {
            "host": host,
            "port": int(port),
            "user": user,
            "password": password,
            "database": database,
        }

    async def initialize(self) -> None:
        """Initialize MySQL connection pool."""
        try:
            logger.info(f"Creating MySQL connection pool (size: {self.pool_size})")
            self._pool = pooling.MySQLConnectionPool(
                pool_name="mcp_pool",
                pool_size=self.pool_size,
                pool_reset_session=True,
                **self._connection_config,
            )
            logger.info("MySQL connection pool created successfully")
        except MySQLError as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise map_driver_error(e, self.driver_type)

    async def close(self) -> None:
        """Close MySQL connection pool."""
        if self._pool:
            logger.info("Closing MySQL connection pool")
            # MySQL connector pool doesn't have explicit close method
            # Connections are closed when pool object is destroyed
            self._pool = None

    @asynccontextmanager
    async def get_connection(self):
        """
        Get MySQL connection from pool.

        Yields:
            mysql.connector.connection object
        """
        if not self._pool:
            raise ConnectionError("Connection pool not initialized", None)

        conn = None
        try:
            conn = self._pool.get_connection()
            yield conn
        except MySQLError as e:
            raise map_driver_error(e, self.driver_type)
        finally:
            if conn:
                conn.close()

    async def execute_query(
        self, query: str, parameters: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute SELECT query against MySQL database."""
        # Validate query safety
        self._validate_query_safety(query)

        # Sanitize parameters
        parameters = self._sanitize_parameters(parameters)

        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                # Set read-only mode if enabled
                if self.read_only:
                    cursor.execute("SET SESSION TRANSACTION READ ONLY")

                # Execute query with parameters
                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)

                # Fetch results
                rows = cursor.fetchall()

                # Convert to list of dicts with serialized values
                columns = cursor.column_names if cursor.column_names else []
                result = [serialize_row(tuple(row.values()), columns) for row in rows]

                cursor.close()
                logger.info(f"MySQL query returned {len(result)} rows")
                return result

        except MySQLError as e:
            logger.error(f"MySQL query error: {e}")
            raise map_driver_error(e, self.driver_type)

    def quote_identifier(self, identifier: str) -> str:
        """
        Quote an identifier using MySQL rules (backticks).
        """
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValidationError("Identifier cannot be empty")

        sanitized = identifier.replace("`", "``")
        return f"`{sanitized}`"

    async def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """List all tables in the MySQL database or specific schema."""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()

                if schema:
                    query = """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = %s
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """
                    cursor.execute(query, (schema,))
                else:
                    # Use current database
                    query = """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = DATABASE()
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """
                    cursor.execute(query)

                tables = [row[0] for row in cursor.fetchall()]
                cursor.close()
                logger.info(f"Found {len(tables)} tables in MySQL database")
                return tables

        except MySQLError as e:
            logger.error(f"Error listing tables: {e}")
            raise map_driver_error(e, self.driver_type)

    async def get_table_schema(
        self, table_name: str, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get column information for a MySQL table."""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()

                # Use specified schema or current database
                if schema:
                    query = """
                        SELECT
                            column_name,
                            data_type,
                            is_nullable,
                            column_default,
                            column_key
                        FROM information_schema.columns
                        WHERE table_schema = %s
                        AND table_name = %s
                        ORDER BY ordinal_position
                    """
                    cursor.execute(query, (schema, table_name))
                else:
                    query = """
                        SELECT
                            column_name,
                            data_type,
                            is_nullable,
                            column_default,
                            column_key
                        FROM information_schema.columns
                        WHERE table_schema = DATABASE()
                        AND table_name = %s
                        ORDER BY ordinal_position
                    """
                    cursor.execute(query, (table_name,))

                columns_info = cursor.fetchall()
                cursor.close()

                if not columns_info:
                    raise NotFoundError(f"Table '{table_name}' not found", "table", table_name)

                # Convert to standardized format
                result = []
                for col in columns_info:
                    result.append(
                        {
                            "name": col[0],
                            "type": col[1],
                            "nullable": col[2] == "YES",
                            "default": col[3],
                            "primary_key": col[4] == "PRI",
                        }
                    )

                logger.info(f"Retrieved schema for table '{table_name}' with {len(result)} columns")
                return result

        except MySQLError as e:
            logger.error(f"Error getting table schema: {e}")
            raise map_driver_error(e, self.driver_type)

    async def get_schemas(self) -> List[str]:
        """List all schemas/databases in the MySQL server."""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
                    ORDER BY schema_name
                """
                cursor.execute(query)
                schemas = [row[0] for row in cursor.fetchall()]
                cursor.close()
                logger.info(f"Found {len(schemas)} schemas in MySQL server")
                return schemas

        except MySQLError as e:
            logger.error(f"Error listing schemas: {e}")
            raise map_driver_error(e, self.driver_type)

    async def test_connection(self) -> Dict[str, Any]:
        """Test MySQL connection and get database info."""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get MySQL version
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]

                # Get current database name
                cursor.execute("SELECT DATABASE()")
                db_name = cursor.fetchone()[0]

                # Count tables
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE()
                    AND table_type = 'BASE TABLE'
                """
                )
                table_count = cursor.fetchone()[0]

                cursor.close()

                return {
                    "connected": True,
                    "database_type": "MySQL",
                    "version": version,
                    "database_name": db_name,
                    "table_count": table_count,
                }

        except MySQLError as e:
            logger.error(f"Connection test failed: {e}")
            return {"connected": False, "database_type": "MySQL", "error": str(e)}

    @property
    def driver_type(self) -> str:
        """Get driver type identifier."""
        return "mysql"

    @property
    def paramstyle(self) -> str:
        """Get parameter style (MySQL uses format: %s)."""
        return "format"
