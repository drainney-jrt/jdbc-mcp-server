"""
Main MCP server implementation using FastMCP.

Provides database connectivity tools for Claude Code via Model Context Protocol.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from jdbc_mcp_server.config import load_config_from_env, mask_credentials
from jdbc_mcp_server.database.base import DatabaseAdapter
from jdbc_mcp_server.database.postgresql import PostgreSQLAdapter
from jdbc_mcp_server.database.mysql import MySQLAdapter
from jdbc_mcp_server.database.sqlite import SQLiteAdapter
from jdbc_mcp_server.database.db2 import DB2Adapter
from jdbc_mcp_server.errors import DatabaseError, ValidationError
from jdbc_mcp_server.utils import (
    truncate_results,
    format_table_schema,
    format_database_schema
)

logger = logging.getLogger(__name__)

# Global dictionary of database adapters
adapters: Dict[str, DatabaseAdapter] = {}


def create_adapter(db_type: str, connection_string: str, read_only: bool = True, pool_size: int = 5) -> DatabaseAdapter:
    """
    Factory function to create database adapters.

    Args:
        db_type: Type of database (postgresql, mysql, sqlite, db2)
        connection_string: Database connection string
        read_only: Whether to enforce read-only mode
        pool_size: Size of connection pool (for network databases)

    Returns:
        DatabaseAdapter instance

    Raises:
        ValueError: If database type is not supported
    """
    if db_type == "postgresql":
        return PostgreSQLAdapter(connection_string, read_only, pool_size)
    elif db_type == "mysql":
        return MySQLAdapter(connection_string, read_only, pool_size)
    elif db_type == "sqlite":
        return SQLiteAdapter(connection_string, read_only)
    elif db_type == "db2":
        return DB2Adapter(connection_string, read_only, pool_size)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


@asynccontextmanager
async def lifespan(app):
    """
    Manage server lifecycle - initialize and cleanup database connections.

    This runs at server startup and shutdown.
    """
    global adapters

    logger.info("Starting JDBC MCP Server...")

    try:
        # Load configuration from environment
        config = load_config_from_env()
        logger.info(f"Loaded configuration for {len(config.databases)} database(s)")

        # Initialize database adapters
        for name, db_config in config.databases.items():
            logger.info(f"Initializing adapter for '{name}' ({db_config.type})")
            logger.info(f"Connection: {mask_credentials(db_config.connection_string)}")

            adapter = create_adapter(
                db_config.type,
                db_config.connection_string,
                db_config.read_only,
                db_config.pool_size
            )

            await adapter.initialize()
            adapters[name] = adapter
            logger.info(f"Adapter '{name}' initialized successfully")

        logger.info("All database adapters initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize server: {e}", exc_info=True)
        raise

    # Server is running
    yield

    # Cleanup on shutdown
    logger.info("Shutting down JDBC MCP Server...")
    for name, adapter in adapters.items():
        try:
            logger.info(f"Closing adapter '{name}'")
            await adapter.close()
        except Exception as e:
            logger.error(f"Error closing adapter '{name}': {e}")

    logger.info("Server shutdown complete")


# Create FastMCP server instance
mcp = FastMCP("Database Server", lifespan=lifespan)


# === MCP TOOLS ===

@mcp.tool()
async def execute_query(
    database: str,
    query: str,
    parameters: Optional[List[Any]] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Execute a SQL SELECT query against a database.

    Args:
        database: Database identifier (e.g., 'postgres', 'sqlite')
        query: SQL SELECT query to execute
        parameters: Optional list of parameter values for query placeholders
        limit: Maximum rows to return (default 100, max 1000)

    Returns:
        Dictionary with query results:
            - success: bool
            - columns: List of column names
            - rows: List of row data
            - row_count: Number of rows returned
            - truncated: Whether results were truncated

    Example:
        execute_query(
            database="postgres",
            query="SELECT * FROM users WHERE id = ?",
            parameters=[123],
            limit=10
        )
    """
    try:
        # Validate database exists
        if database not in adapters:
            available = ", ".join(adapters.keys())
            raise ValidationError(
                f"Database '{database}' not configured. "
                f"Available databases: {available}"
            )

        adapter = adapters[database]

        # Convert parameters list to tuple
        params_tuple = tuple(parameters) if parameters else None

        # Execute query
        rows = await adapter.execute_query(query, params_tuple)

        # Extract column names from first row
        columns = list(rows[0].keys()) if rows else []

        # Convert rows to list of lists for cleaner output
        row_data = [list(row.values()) for row in rows]

        # Truncate results if needed
        truncated_rows, was_truncated = truncate_results(row_data, limit)

        return {
            "success": True,
            "columns": columns,
            "rows": truncated_rows,
            "row_count": len(truncated_rows),
            "truncated": was_truncated,
            "total_rows_before_limit": len(row_data)
        }

    except DatabaseError as e:
        logger.error(f"Query execution failed: {e}")
        return {
            "success": False,
            **e.to_mcp_error()
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "category": "unknown_error"
        }


@mcp.tool()
async def list_tables(
    database: str,
    schema: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all tables in a database or schema.

    Args:
        database: Database identifier
        schema: Optional schema name (PostgreSQL/MySQL only)

    Returns:
        Dictionary with table list:
            - success: bool
            - tables: List of table names
            - table_count: Number of tables

    Example:
        list_tables(database="postgres", schema="public")
    """
    try:
        if database not in adapters:
            available = ", ".join(adapters.keys())
            raise ValidationError(
                f"Database '{database}' not configured. "
                f"Available databases: {available}"
            )

        adapter = adapters[database]
        tables = await adapter.get_tables(schema)

        return {
            "success": True,
            "tables": tables,
            "table_count": len(tables),
            "schema": schema
        }

    except DatabaseError as e:
        logger.error(f"List tables failed: {e}")
        return {
            "success": False,
            **e.to_mcp_error()
        }


@mcp.tool()
async def describe_table(
    database: str,
    table: str,
    schema: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get detailed schema information for a table.

    Args:
        database: Database identifier
        table: Table name
        schema: Optional schema name

    Returns:
        Dictionary with table schema:
            - success: bool
            - table_name: str
            - schema: str
            - columns: List of column metadata

    Example:
        describe_table(database="postgres", table="users", schema="public")
    """
    try:
        if database not in adapters:
            available = ", ".join(adapters.keys())
            raise ValidationError(
                f"Database '{database}' not configured. "
                f"Available databases: {available}"
            )

        adapter = adapters[database]
        columns = await adapter.get_table_schema(table, schema)

        return {
            "success": True,
            "table_name": table,
            "schema": schema,
            "columns": columns,
            "column_count": len(columns)
        }

    except DatabaseError as e:
        logger.error(f"Describe table failed: {e}")
        return {
            "success": False,
            **e.to_mcp_error()
        }


@mcp.tool()
async def test_connection(database: str) -> Dict[str, Any]:
    """
    Test database connectivity and get server information.

    Args:
        database: Database identifier

    Returns:
        Dictionary with connection status and metadata

    Example:
        test_connection(database="postgres")
    """
    try:
        if database not in adapters:
            available = ", ".join(adapters.keys())
            raise ValidationError(
                f"Database '{database}' not configured. "
                f"Available databases: {available}"
            )

        adapter = adapters[database]
        result = await adapter.test_connection()

        return {
            "success": True,
            **result
        }

    except DatabaseError as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "success": False,
            **e.to_mcp_error()
        }


@mcp.tool()
async def get_sample_data(
    database: str,
    table: str,
    schema: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get sample rows from a table.

    Args:
        database: Database identifier
        table: Table name
        schema: Optional schema name
        limit: Number of sample rows (default 10, max 100)

    Returns:
        Dictionary with sample data

    Example:
        get_sample_data(database="postgres", table="users", limit=5)
    """
    try:
        if database not in adapters:
            available = ", ".join(adapters.keys())
            raise ValidationError(
                f"Database '{database}' not configured. "
                f"Available databases: {available}"
            )

        adapter = adapters[database]

        # Build query based on schema
        if schema:
            full_table_name = f"{schema}.{table}"
        else:
            full_table_name = table

        # Limit to max 100 rows
        effective_limit = min(limit, 100)

        query = f"SELECT * FROM {full_table_name} LIMIT {effective_limit}"
        rows = await adapter.execute_query(query, None)

        # Extract columns
        columns = list(rows[0].keys()) if rows else []
        row_data = [list(row.values()) for row in rows]

        return {
            "success": True,
            "table": table,
            "schema": schema,
            "columns": columns,
            "rows": row_data,
            "row_count": len(row_data)
        }

    except DatabaseError as e:
        logger.error(f"Get sample data failed: {e}")
        return {
            "success": False,
            **e.to_mcp_error()
        }


@mcp.tool()
async def list_schemas(database: str) -> Dict[str, Any]:
    """
    List all schemas/databases for the database server.

    Args:
        database: Database identifier

    Returns:
        Dictionary with schema list:
            - success: bool
            - schemas: List of schema names
            - schema_count: Number of schemas

    Example:
        list_schemas(database="postgres")
    """
    try:
        if database not in adapters:
            available = ", ".join(adapters.keys())
            raise ValidationError(
                f"Database '{database}' not configured. "
                f"Available databases: {available}"
            )

        adapter = adapters[database]
        schemas = await adapter.get_schemas()

        return {
            "success": True,
            "schemas": schemas,
            "schema_count": len(schemas)
        }

    except DatabaseError as e:
        logger.error(f"List schemas failed: {e}")
        return {
            "success": False,
            **e.to_mcp_error()
        }


@mcp.tool()
async def list_databases() -> Dict[str, Any]:
    """
    List all configured database connections.

    Returns:
        Dictionary with database list:
            - success: bool
            - databases: List of configured database names
            - database_count: Number of configured databases

    Example:
        list_databases()
    """
    try:
        db_list = []
        for name, adapter in adapters.items():
            db_list.append({
                "name": name,
                "type": adapter.driver_type,
                "read_only": adapter.read_only
            })

        return {
            "success": True,
            "databases": db_list,
            "database_count": len(db_list)
        }

    except Exception as e:
        logger.error(f"List databases failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# === MCP RESOURCES ===

@mcp.resource("db://{database}/schema")
async def get_database_schema(database: str) -> str:
    """
    Get complete database schema as formatted markdown.

    Args:
        database: Database identifier

    Returns:
        Formatted markdown with all tables
    """
    if database not in adapters:
        return f"Error: Database '{database}' not configured"

    try:
        adapter = adapters[database]
        tables = await adapter.get_tables()
        return format_database_schema(tables, database)
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"


@mcp.resource("db://{database}/tables/{table}/schema")
async def get_table_schema_resource(database: str, table: str) -> str:
    """
    Get table schema as formatted markdown.

    Args:
        database: Database identifier
        table: Table name

    Returns:
        Formatted markdown with column definitions
    """
    if database not in adapters:
        return f"Error: Database '{database}' not configured"

    try:
        adapter = adapters[database]
        schema = await adapter.get_table_schema(table)
        return format_table_schema(schema, table)
    except Exception as e:
        return f"Error retrieving table schema: {str(e)}"


# === MCP PROMPTS ===

@mcp.prompt()
def explore_database() -> str:
    """
    Guided database exploration workflow.

    Returns:
        Instructions for exploring a database
    """
    return """Let's explore a database together:

1. First, use `list_databases()` to see all configured database connections
2. Choose a database and use `test_connection(database="name")` to verify connectivity
3. Use `list_schemas(database="name")` to see available schemas (if applicable)
4. Use `list_tables(database="name")` to see all tables
5. For interesting tables, use `describe_table(database="name", table="table_name")` to see the structure
6. Use `get_sample_data(database="name", table="table_name", limit=5)` to preview the data
7. Based on the schema, suggest useful queries to extract insights

Remember: All databases are in read-only mode by default for safety.
"""


@mcp.prompt()
def query_with_safety() -> str:
    """
    Generate safe parameterized queries.

    Returns:
        Instructions for safe query generation
    """
    return """Help me query a database safely:

1. I'll describe what data I need from which database
2. Generate a SELECT query using parameterized placeholders:
   - For PostgreSQL/MySQL: Use %s or %(name)s
   - For SQLite: Use ?
3. Provide the query and parameters separately
4. Use `execute_query(database="name", query="...", parameters=[...])` to run it
5. Format the results in a readable table
6. Suggest follow-up queries based on the results

Safety rules:
- Only SELECT queries are allowed (databases are read-only)
- Always use parameterized queries to prevent SQL injection
- Never concatenate user input directly into SQL
"""


@mcp.prompt()
def analyze_table_structure() -> str:
    """
    Analyze table structure and relationships.

    Returns:
        Instructions for analyzing database structure
    """
    return """I need to analyze a database table structure:

1. Start with `list_databases()` to see available databases
2. Choose a database and use `list_tables(database="name")` to see all tables
3. For the table I specify, use `describe_table(database="name", table="table_name")`
4. Analyze the schema:
   - Identify primary keys and their types
   - Look for foreign key naming patterns (columns ending in _id, _key, etc.)
   - Note nullable vs non-nullable columns
   - Identify data types and their implications
5. Suggest potential relationships with other tables based on column names
6. Recommend queries to validate these relationships
7. Provide sample queries to explore the data

Focus on understanding the data model and how tables relate to each other.
"""
