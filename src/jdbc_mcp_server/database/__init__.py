"""
Database adapters for different database types.

Each adapter implements the DatabaseAdapter interface and handles
database-specific connection management, query execution, and schema introspection.
"""

from jdbc_mcp_server.database.base import DatabaseAdapter
from jdbc_mcp_server.database.postgresql import PostgreSQLAdapter
from jdbc_mcp_server.database.mysql import MySQLAdapter
from jdbc_mcp_server.database.sqlite import SQLiteAdapter
from jdbc_mcp_server.database.db2 import DB2Adapter

__all__ = [
    "DatabaseAdapter",
    "PostgreSQLAdapter",
    "MySQLAdapter",
    "SQLiteAdapter",
    "DB2Adapter"
]
