"""
Utility functions for serialization, validation, and data conversion.
"""

import decimal
import datetime
from typing import Any, Dict, List, Tuple


def serialize_value(value: Any) -> Any:
    """
    Convert database types to JSON-serializable types.

    Args:
        value: Value from database query result

    Returns:
        JSON-serializable value
    """
    if value is None:
        return None

    # Convert Decimal to float
    if isinstance(value, decimal.Decimal):
        return float(value)

    # Convert dates and datetimes to ISO format strings
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()

    # Convert time to string
    if isinstance(value, datetime.time):
        return value.isoformat()

    # Convert bytes to string (attempt UTF-8, fallback to latin-1)
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            return value.decode('latin-1', errors='replace')

    # Convert memoryview to bytes then string
    if isinstance(value, memoryview):
        try:
            return bytes(value).decode('utf-8')
        except UnicodeDecodeError:
            return bytes(value).decode('latin-1', errors='replace')

    return value


def serialize_row(row: Tuple, columns: List[str]) -> Dict[str, Any]:
    """
    Convert a database row tuple to a dictionary with serialized values.

    Args:
        row: Tuple of values from database query
        columns: List of column names

    Returns:
        Dictionary mapping column names to serialized values
    """
    return {
        col: serialize_value(val)
        for col, val in zip(columns, row)
    }


def format_table_schema(schema: List[Dict[str, Any]], table_name: str) -> str:
    """
    Format table schema as readable markdown.

    Args:
        schema: List of column metadata dictionaries
        table_name: Name of the table

    Returns:
        Formatted markdown string
    """
    lines = [f"# Table: {table_name}\n"]

    if not schema:
        lines.append("*No columns found*\n")
        return "\n".join(lines)

    lines.append("| Column | Type | Nullable | Primary Key | Default |")
    lines.append("|--------|------|----------|-------------|---------|")

    for col in schema:
        name = col.get('name', 'unknown')
        col_type = col.get('type', 'unknown')
        nullable = "Yes" if col.get('nullable', True) else "No"
        pk = "Yes" if col.get('primary_key', False) else "No"
        default = col.get('default', '-')

        lines.append(f"| {name} | {col_type} | {nullable} | {pk} | {default} |")

    return "\n".join(lines)


def format_database_schema(tables: List[str], db_name: str) -> str:
    """
    Format complete database schema as readable markdown.

    Args:
        tables: List of table names
        db_name: Name of the database

    Returns:
        Formatted markdown string
    """
    lines = [f"# Database: {db_name}\n"]

    if not tables:
        lines.append("*No tables found*\n")
        return "\n".join(lines)

    lines.append(f"**Total Tables:** {len(tables)}\n")
    lines.append("## Tables\n")

    for table in sorted(tables):
        lines.append(f"- {table}")

    return "\n".join(lines)


def truncate_results(
    rows: List[Dict[str, Any]],
    limit: int = 100,
    max_limit: int = 1000
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Truncate query results to specified limit.

    Args:
        rows: List of result rows
        limit: Desired limit (default: 100)
        max_limit: Maximum allowed limit (default: 1000)

    Returns:
        Tuple of (truncated_rows, was_truncated)
    """
    # Enforce maximum limit
    effective_limit = min(limit, max_limit)

    if len(rows) > effective_limit:
        return rows[:effective_limit], True
    else:
        return rows, False
