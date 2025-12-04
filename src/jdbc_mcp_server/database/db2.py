"""
DB2 database adapter implementation.

Uses ibm_db driver for DB2 iSeries database connectivity.
Note: ibm_db is synchronous and doesn't support connection pooling natively,
so we manage connections manually.
"""

import ibm_db
import ibm_db_dbi
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple
import logging

from jdbc_mcp_server.database.base import DatabaseAdapter
from jdbc_mcp_server.errors import ConnectionError, QueryError, NotFoundError, map_driver_error
from jdbc_mcp_server.utils import serialize_row

logger = logging.getLogger(__name__)


class DB2Adapter(DatabaseAdapter):
    """DB2 database adapter using ibm_db driver."""

    def __init__(self, connection_string: str, read_only: bool = True, pool_size: int = 5):
        """
        Initialize DB2 adapter.

        Args:
            connection_string: DB2 connection string
                              (e.g., "DATABASE=mydb;HOSTNAME=localhost;PORT=50000;PROTOCOL=TCPIP;UID=user;PWD=pass;")
            read_only: Whether to enforce read-only mode
            pool_size: Number of connections in the pool (managed manually)
        """
        super().__init__(connection_string, read_only)
        self.pool_size = pool_size
        self._connections: List[Any] = []
        logger.info(f"DB2 adapter initialized with pool size: {pool_size}")

    async def initialize(self) -> None:
        """Initialize DB2 connection pool (manual pooling)."""
        try:
            logger.info(f"Creating DB2 connection pool (size: {self.pool_size})")
            # Pre-create connections for the pool
            for i in range(self.pool_size):
                conn = ibm_db.connect(self.connection_string, "", "")
                if conn:
                    self._connections.append(conn)
                    logger.debug(f"Created DB2 connection {i+1}/{self.pool_size}")
                else:
                    raise ConnectionError("Failed to create DB2 connection", None)
            logger.info("DB2 connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise map_driver_error(e, self.driver_type)

    async def close(self) -> None:
        """Close DB2 connection pool."""
        if self._connections:
            logger.info("Closing DB2 connection pool")
            for conn in self._connections:
                try:
                    ibm_db.close(conn)
                except Exception as e:
                    logger.warning(f"Error closing DB2 connection: {e}")
            self._connections = []

    @asynccontextmanager
    async def get_connection(self):
        """
        Get DB2 connection from pool.

        Yields:
            ibm_db connection object
        """
        if not self._connections:
            raise ConnectionError("Connection pool not initialized", None)

        # Get a connection from the pool (simple round-robin)
        conn = self._connections[0] if self._connections else None
        if not conn:
            raise ConnectionError("No available connections in pool", None)

        try:
            yield conn
        except Exception as e:
            raise map_driver_error(e, self.driver_type)

    async def execute_query(
        self, query: str, parameters: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute SELECT query against DB2 database."""
        # Validate query safety
        self._validate_query_safety(query)

        # Sanitize parameters
        parameters = self._sanitize_parameters(parameters)

        try:
            async with self.get_connection() as conn:
                # Use DB-API interface for easier query execution
                dbi_conn = ibm_db_dbi.Connection(conn)
                cursor = dbi_conn.cursor()

                # Execute query with parameters
                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)

                # Fetch results
                rows = cursor.fetchall()

                # Get column names
                columns = [desc[0] for desc in cursor.description] if cursor.description else []

                # Convert to list of dicts with serialized values
                result = [serialize_row(row, columns) for row in rows]

                cursor.close()
                logger.info(f"DB2 query returned {len(result)} rows")
                return result

        except Exception as e:
            logger.error(f"DB2 query error: {e}")
            raise map_driver_error(e, self.driver_type)

    async def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """List all tables in the DB2 database or specific schema."""
        try:
            async with self.get_connection() as conn:
                # Use ibm_db.tables to list tables
                if schema:
                    stmt = ibm_db.tables(conn, None, schema.upper(), None, "TABLE")
                else:
                    stmt = ibm_db.tables(conn, None, None, None, "TABLE")

                tables = []
                result = ibm_db.fetch_assoc(stmt)
                while result:
                    table_name = result["TABLE_NAME"]
                    table_schema = result["TABLE_SCHEM"]
                    # Skip system tables
                    if not table_schema.startswith("SYS"):
                        tables.append(table_name)
                    result = ibm_db.fetch_assoc(stmt)

                ibm_db.free_result(stmt)
                logger.info(f"Found {len(tables)} tables in DB2 database")
                return sorted(tables)

        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            raise map_driver_error(e, self.driver_type)

    async def get_table_schema(
        self, table_name: str, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get column information for a DB2 table."""
        try:
            async with self.get_connection() as conn:
                # Use ibm_db.columns to get column information
                if schema:
                    stmt = ibm_db.columns(conn, None, schema.upper(), table_name.upper())
                else:
                    stmt = ibm_db.columns(conn, None, None, table_name.upper())

                columns_info = []
                result = ibm_db.fetch_assoc(stmt)
                while result:
                    columns_info.append(result)
                    result = ibm_db.fetch_assoc(stmt)

                ibm_db.free_result(stmt)

                if not columns_info:
                    raise NotFoundError(f"Table '{table_name}' not found", "table", table_name)

                # Get primary key information
                if schema:
                    pk_stmt = ibm_db.primary_keys(conn, None, schema.upper(), table_name.upper())
                else:
                    pk_stmt = ibm_db.primary_keys(conn, None, None, table_name.upper())

                primary_keys = set()
                pk_result = ibm_db.fetch_assoc(pk_stmt)
                while pk_result:
                    primary_keys.add(pk_result["COLUMN_NAME"])
                    pk_result = ibm_db.fetch_assoc(pk_stmt)

                ibm_db.free_result(pk_stmt)

                # Convert to standardized format
                result = []
                for col in columns_info:
                    result.append(
                        {
                            "name": col["COLUMN_NAME"],
                            "type": col["TYPE_NAME"],
                            "nullable": col["NULLABLE"] == 1,
                            "default": col.get("COLUMN_DEF"),
                            "primary_key": col["COLUMN_NAME"] in primary_keys,
                        }
                    )

                logger.info(f"Retrieved schema for table '{table_name}' with {len(result)} columns")
                return result

        except Exception as e:
            logger.error(f"Error getting table schema: {e}")
            raise map_driver_error(e, self.driver_type)

    async def get_schemas(self) -> List[str]:
        """List all schemas in the DB2 database."""
        try:
            async with self.get_connection() as conn:
                dbi_conn = ibm_db_dbi.Connection(conn)
                cursor = dbi_conn.cursor()

                # Query system catalog for schemas
                query = """
                    SELECT SCHEMANAME
                    FROM SYSCAT.SCHEMATA
                    WHERE SCHEMANAME NOT LIKE 'SYS%'
                    ORDER BY SCHEMANAME
                """
                cursor.execute(query)
                schemas = [row[0] for row in cursor.fetchall()]
                cursor.close()
                logger.info(f"Found {len(schemas)} schemas in DB2 database")
                return schemas

        except Exception as e:
            logger.error(f"Error listing schemas: {e}")
            # If SYSCAT is not available, return empty list
            logger.warning("Unable to query DB2 system catalog, returning empty schema list")
            return []

    async def test_connection(self) -> Dict[str, Any]:
        """Test DB2 connection and get database info."""
        try:
            async with self.get_connection() as conn:
                # Get DB2 server information
                server_info = ibm_db.server_info(conn)

                dbi_conn = ibm_db_dbi.Connection(conn)
                cursor = dbi_conn.cursor()

                # Get current schema
                cursor.execute("SELECT CURRENT SCHEMA FROM SYSIBM.SYSDUMMY1")
                current_schema = cursor.fetchone()[0]

                # Count tables (attempt - may fail on some DB2 systems)
                try:
                    cursor.execute(
                        """
                        SELECT COUNT(*)
                        FROM SYSCAT.TABLES
                        WHERE TYPE = 'T'
                        AND TABSCHEMA NOT LIKE 'SYS%'
                    """
                    )
                    table_count = cursor.fetchone()[0]
                except:
                    table_count = 0

                cursor.close()

                return {
                    "connected": True,
                    "database_type": "DB2",
                    "version": f"{server_info.DBMS_NAME} {server_info.DBMS_VER}",
                    "database_name": server_info.DB_NAME,
                    "current_schema": current_schema.strip(),
                    "table_count": table_count,
                }

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {"connected": False, "database_type": "DB2", "error": str(e)}

    @property
    def driver_type(self) -> str:
        """Get driver type identifier."""
        return "db2"

    @property
    def paramstyle(self) -> str:
        """Get parameter style (DB2 uses qmark: ?)."""
        return "qmark"
