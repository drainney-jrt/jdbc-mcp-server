"""
PostgreSQL database adapter implementation.

Uses psycopg2 with connection pooling for efficient connection management.
"""

import psycopg2
import psycopg2.pool
import psycopg2.extras
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple
import logging

from jdbc_mcp_server.database.base import DatabaseAdapter
from jdbc_mcp_server.errors import ConnectionError, QueryError, NotFoundError, map_driver_error
from jdbc_mcp_server.utils import serialize_row

logger = logging.getLogger(__name__)


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter using psycopg2 with connection pooling."""

    def __init__(self, connection_string: str, read_only: bool = True, pool_size: int = 5):
        """
        Initialize PostgreSQL adapter.

        Args:
            connection_string: PostgreSQL connection string
                              (e.g., "postgresql://user:pass@localhost:5432/database")
            read_only: Whether to enforce read-only mode
            pool_size: Number of connections in the pool
        """
        super().__init__(connection_string, read_only)
        self.pool_size = pool_size
        self._pool = None
        logger.info(f"PostgreSQL adapter initialized with pool size: {pool_size}")

    async def initialize(self) -> None:
        """Initialize PostgreSQL connection pool."""
        try:
            logger.info(f"Creating PostgreSQL connection pool (size: {self.pool_size})")
            self._pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=self.pool_size,
                dsn=self.connection_string
            )
            logger.info("PostgreSQL connection pool created successfully")
        except psycopg2.Error as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise map_driver_error(e, self.driver_type)

    async def close(self) -> None:
        """Close PostgreSQL connection pool."""
        if self._pool:
            logger.info("Closing PostgreSQL connection pool")
            self._pool.closeall()
            self._pool = None

    @asynccontextmanager
    async def get_connection(self):
        """
        Get PostgreSQL connection from pool.

        Yields:
            psycopg2.connection object
        """
        if not self._pool:
            raise ConnectionError("Connection pool not initialized", None)

        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        except psycopg2.Error as e:
            raise map_driver_error(e, self.driver_type)
        finally:
            if conn:
                self._pool.putconn(conn)

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute SELECT query against PostgreSQL database."""
        # Validate query safety
        self._validate_query_safety(query)

        # Sanitize parameters
        parameters = self._sanitize_parameters(parameters)

        try:
            async with self.get_connection() as conn:
                # Set transaction to read-only if in read-only mode
                if self.read_only:
                    with conn.cursor() as cursor:
                        cursor.execute("SET TRANSACTION READ ONLY")

                # Execute query
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    if parameters:
                        cursor.execute(query, parameters)
                    else:
                        cursor.execute(query)

                    # Fetch results
                    rows = cursor.fetchall()

                    # Convert to list of dicts with serialized values
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    result = [serialize_row(tuple(row.values()), columns) for row in rows]

                    logger.info(f"PostgreSQL query returned {len(result)} rows")
                    return result

        except psycopg2.Error as e:
            logger.error(f"PostgreSQL query error: {e}")
            raise map_driver_error(e, self.driver_type)

    async def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """List all tables in the PostgreSQL database or specific schema."""
        try:
            async with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    if schema:
                        query = """
                            SELECT tablename
                            FROM pg_tables
                            WHERE schemaname = %s
                            ORDER BY tablename
                        """
                        cursor.execute(query, (schema,))
                    else:
                        query = """
                            SELECT tablename
                            FROM pg_tables
                            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                            ORDER BY tablename
                        """
                        cursor.execute(query)

                    tables = [row[0] for row in cursor.fetchall()]
                    logger.info(f"Found {len(tables)} tables in PostgreSQL database")
                    return tables

        except psycopg2.Error as e:
            logger.error(f"Error listing tables: {e}")
            raise map_driver_error(e, self.driver_type)

    async def get_table_schema(
        self,
        table_name: str,
        schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get column information for a PostgreSQL table."""
        try:
            async with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Default to public schema if not specified
                    schema_name = schema or 'public'

                    query = """
                        SELECT
                            c.column_name,
                            c.data_type,
                            c.is_nullable,
                            c.column_default,
                            CASE
                                WHEN pk.column_name IS NOT NULL THEN true
                                ELSE false
                            END as is_primary_key
                        FROM information_schema.columns c
                        LEFT JOIN (
                            SELECT ku.column_name
                            FROM information_schema.table_constraints tc
                            JOIN information_schema.key_column_usage ku
                                ON tc.constraint_name = ku.constraint_name
                                AND tc.table_schema = ku.table_schema
                            WHERE tc.constraint_type = 'PRIMARY KEY'
                                AND tc.table_schema = %s
                                AND tc.table_name = %s
                        ) pk ON c.column_name = pk.column_name
                        WHERE c.table_schema = %s
                            AND c.table_name = %s
                        ORDER BY c.ordinal_position
                    """

                    cursor.execute(query, (schema_name, table_name, schema_name, table_name))
                    columns_info = cursor.fetchall()

                    if not columns_info:
                        raise NotFoundError(
                            f"Table '{schema_name}.{table_name}' not found",
                            "table",
                            table_name
                        )

                    # Convert to standardized format
                    result = []
                    for col in columns_info:
                        result.append({
                            'name': col[0],
                            'type': col[1],
                            'nullable': col[2] == 'YES',
                            'default': col[3],
                            'primary_key': col[4]
                        })

                    logger.info(f"Retrieved schema for table '{table_name}' with {len(result)} columns")
                    return result

        except psycopg2.Error as e:
            logger.error(f"Error getting table schema: {e}")
            raise map_driver_error(e, self.driver_type)

    async def get_schemas(self) -> List[str]:
        """List all schemas in the PostgreSQL database."""
        try:
            async with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT schema_name
                        FROM information_schema.schemata
                        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                        ORDER BY schema_name
                    """
                    cursor.execute(query)
                    schemas = [row[0] for row in cursor.fetchall()]
                    logger.info(f"Found {len(schemas)} schemas in PostgreSQL database")
                    return schemas

        except psycopg2.Error as e:
            logger.error(f"Error listing schemas: {e}")
            raise map_driver_error(e, self.driver_type)

    async def test_connection(self) -> Dict[str, Any]:
        """Test PostgreSQL connection and get database info."""
        try:
            async with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get PostgreSQL version
                    cursor.execute("SELECT version()")
                    version_string = cursor.fetchone()[0]
                    version = version_string.split(' ')[1] if ' ' in version_string else version_string

                    # Get current database name
                    cursor.execute("SELECT current_database()")
                    db_name = cursor.fetchone()[0]

                    # Count tables
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM pg_tables
                        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                    """)
                    table_count = cursor.fetchone()[0]

                    return {
                        'connected': True,
                        'database_type': 'PostgreSQL',
                        'version': version,
                        'database_name': db_name,
                        'table_count': table_count
                    }

        except psycopg2.Error as e:
            logger.error(f"Connection test failed: {e}")
            return {
                'connected': False,
                'database_type': 'PostgreSQL',
                'error': str(e)
            }

    @property
    def driver_type(self) -> str:
        """Get driver type identifier."""
        return "postgresql"

    @property
    def paramstyle(self) -> str:
        """Get parameter style (PostgreSQL uses pyformat: %(name)s)."""
        return "pyformat"
