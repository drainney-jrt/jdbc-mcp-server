import pytest
from jdbc_mcp_server.database.base import DatabaseAdapter
from jdbc_mcp_server.errors import SecurityError, ValidationError

class ConcreteAdapter(DatabaseAdapter):
    """A concrete implementation of DatabaseAdapter for testing."""
    driver_type = "test"
    paramstyle = "qmark"

    def __init__(self, connection_string: str, read_only: bool = True):
        super().__init__(connection_string, read_only)

    async def initialize(self):
        pass

    async def close(self):
        pass

    async def get_connection(self):
        pass

    async def execute_query(self, query, params=None):
        return []

    async def get_tables(self, schema=None):
        return []

    async def get_table_schema(self, table, schema=None):
        return []

    def quote_identifier(self, identifier: str) -> str:
        return f'"{identifier}"'

    async def get_schemas(self):
        return []

    async def test_connection(self):
        return {}


def test_validate_query_safety_readonly_mode_allowed():
    """
    Test that allowed SELECT statements pass in read-only mode.
    """
    adapter = ConcreteAdapter("conn_str", read_only=True)
    adapter._validate_query_safety("SELECT * FROM users")
    adapter._validate_query_safety("   select * from users")
    adapter._validate_query_safety("WITH cte AS (SELECT 1) SELECT * FROM cte")


def test_validate_query_safety_readonly_mode_disallowed():
    """
    Test that disallowed statements fail in read-only mode.
    """
    adapter = ConcreteAdapter("conn_str", read_only=True)
    disallowed = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "TRUNCATE", "GRANT", "EXEC"]
    for statement in disallowed:
        with pytest.raises(SecurityError):
            adapter._validate_query_safety(f"{statement} INTO users VALUES (1)")


def test_validate_query_safety_writable_mode():
    """
    Test that INSERT, UPDATE, DELETE pass when read_only is False.
    """
    adapter = ConcreteAdapter("conn_str", read_only=False)
    adapter._validate_query_safety("INSERT INTO users VALUES (1)")
    adapter._validate_query_safety("UPDATE users SET name = 'new' WHERE id = 1")
    adapter._validate_query_safety("DELETE FROM users WHERE id = 1")


def test_validate_query_multiple_statements():
    """
    Test that multiple statements in a single query are rejected.
    """
    adapter = ConcreteAdapter("conn_str", read_only=True)
    with pytest.raises(SecurityError):
        adapter._validate_query_safety("SELECT * FROM users; DELETE FROM users")


def test_validate_query_comments():
    """
    Test that queries with comments are rejected.
    """
    adapter = ConcreteAdapter("conn_str", read_only=True)
    with pytest.raises(SecurityError):
        adapter._validate_query_safety("SELECT * FROM users; -- DROP TABLE users")
    with pytest.raises(SecurityError):
        adapter._validate_query_safety("/* comment */ SELECT * FROM users")

def test_empty_query():
    """
    Test that an empty query raises a validation error.
    """
    adapter = ConcreteAdapter("conn_str", read_only=True)
    with pytest.raises(ValidationError):
        adapter._validate_query_safety("")
    with pytest.raises(ValidationError):
        adapter._validate_query_safety("   ")