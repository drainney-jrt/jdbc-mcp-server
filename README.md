# Common Database MCP Server

A Model Context Protocol (MCP) server that provides database connectivity to Claude Code, Claude Desktop, and Windsurf IDE. Supports PostgreSQL, MySQL, SQLite, and DB2 iSeries databases through native Python drivers.

## Features

- ✅ **Multiple Database Support**: PostgreSQL, MySQL, SQLite, DB2 iSeries
- ✅ **Read-Only by Default**: Safe database exploration without risk of data modification
- ✅ **Connection Pooling**: Efficient connection management for network databases
- ✅ **SQL Injection Prevention**: Parameterized queries and query validation
- ✅ **Cross-Platform**: Works on macOS, Linux, and Windows
- ✅ **MCP Tools**: Execute queries, inspect schemas, explore tables
- ✅ **MCP Resources**: Database schemas as resources
- ✅ **MCP Prompts**: Guided workflows for database exploration

## Installation

### Prerequisites

- Python 3.9 or higher
- pip

### Install from Source

```bash
cd /Users/dave/claude-projects/jdbc-mcp-server
pip install -e .
```

### Install Optional Dependencies

For development and testing:

```bash
pip install -e ".[dev]"
```

### Database Driver Installation

The server automatically installs drivers for:
- PostgreSQL (`psycopg2-binary`)
- MySQL (`mysql-connector-python`)
- SQLite (`sqlite3` - built into Python)

For **DB2 iSeries on macOS**:

```bash
# DB2 driver installation
pip install --no-cache-dir ibm_db
```

Note: `ibm_db` works on macOS (both Intel and Apple Silicon M1/M2/M3).

## Configuration

### Claude Code Configuration

Add the server to your `~/.claude/mcp.json` or Claude Desktop configuration:

```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "jdbc_mcp_server"],
      "env": {
        "DB_POSTGRES_TYPE": "postgresql",
        "DB_POSTGRES_HOST": "localhost",
        "DB_POSTGRES_PORT": "5432",
        "DB_POSTGRES_DATABASE": "myapp",
        "DB_POSTGRES_USERNAME": "readonly_user",
        "DB_POSTGRES_PASSWORD": "secure_password",
        "DB_POSTGRES_READ_ONLY": "true",
        "DB_POSTGRES_POOL_SIZE": "10"
      }
    }
  }
}
```

### Environment Variables

Configure databases using environment variables with the format:

```bash
DB_<NAME>_TYPE=postgresql|mysql|sqlite|db2
DB_<NAME>_HOST=hostname
DB_<NAME>_PORT=port
DB_<NAME>_DATABASE=database_name
DB_<NAME>_USERNAME=username
DB_<NAME>_PASSWORD=password
DB_<NAME>_READ_ONLY=true|false
DB_<NAME>_POOL_SIZE=5
```

Or use connection strings:

```bash
DB_<NAME>_TYPE=postgresql
DB_<NAME>_CONNECTION_STRING=postgresql://user:pass@localhost:5432/database
```

### Multiple Database Example

Configure multiple databases:

```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "jdbc_mcp_server"],
      "env": {
        "DB_PROD_TYPE": "postgresql",
        "DB_PROD_CONNECTION_STRING": "postgresql://readonly@prod-server:5432/production",
        "DB_PROD_READ_ONLY": "true",

        "DB_LOCAL_TYPE": "sqlite",
        "DB_LOCAL_PATH": "/Users/dave/data/local.db",
        "DB_LOCAL_READ_ONLY": "false",

        "DB_ANALYTICS_TYPE": "mysql",
        "DB_ANALYTICS_HOST": "analytics.example.com",
        "DB_ANALYTICS_PORT": "3306",
        "DB_ANALYTICS_DATABASE": "analytics",
        "DB_ANALYTICS_USERNAME": "analyst",
        "DB_ANALYTICS_PASSWORD": "password"
      }
    }
  }
}
```

## Usage

### Available MCP Tools

#### `list_databases()`
List all configured database connections.

```python
list_databases()
# Returns: {"success": True, "databases": [{"name": "prod", "type": "postgresql", "read_only": True}, ...]}
```

#### `test_connection(database)`
Test database connectivity.

```python
test_connection(database="prod")
# Returns: {"success": True, "connected": True, "database_type": "PostgreSQL", "version": "15.2", ...}
```

#### `list_schemas(database)`
List all schemas/databases (PostgreSQL/MySQL only).

```python
list_schemas(database="prod")
# Returns: {"success": True, "schemas": ["public", "app", ...]}
```

#### `list_tables(database, schema=None)`
List all tables in a database.

```python
list_tables(database="prod", schema="public")
# Returns: {"success": True, "tables": ["users", "orders", ...]}
```

#### `describe_table(database, table, schema=None)`
Get detailed table schema.

```python
describe_table(database="prod", table="users", schema="public")
# Returns: {"success": True, "columns": [{"name": "id", "type": "integer", "nullable": False, "primary_key": True}, ...]}
```

#### `execute_query(database, query, parameters=None, limit=100)`
Execute a SELECT query with parameterized inputs.

```python
execute_query(
    database="prod",
    query="SELECT * FROM users WHERE status = %s AND created_at > %s",
    parameters=["active", "2024-01-01"],
    limit=50
)
# Returns: {"success": True, "columns": [...], "rows": [...], "row_count": 50}
```

#### `get_sample_data(database, table, schema=None, limit=10)`
Get sample rows from a table.

```python
get_sample_data(database="prod", table="users", limit=5)
# Returns: {"success": True, "columns": [...], "rows": [...]}
```

### Available MCP Resources

#### `db://{database}/schema`
Get complete database schema as markdown.

#### `db://{database}/tables/{table}/schema`
Get specific table schema as markdown.

### Available MCP Prompts

#### `explore_database`
Guided workflow for database exploration.

#### `query_with_safety`
Instructions for generating safe parameterized queries.

#### `analyze_table_structure`
Analyze table structure and identify relationships.

## Security Best Practices

### 1. Use Read-Only Mode

Always use read-only mode (default) when exploring production databases:

```bash
DB_PROD_READ_ONLY=true
```

### 2. Create Dedicated Database Users

Create database users with SELECT-only permissions:

**PostgreSQL:**
```sql
CREATE USER readonly_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE myapp TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;
```

**MySQL:**
```sql
CREATE USER 'readonly_user'@'%' IDENTIFIED BY 'secure_password';
GRANT SELECT ON myapp.* TO 'readonly_user'@'%';
FLUSH PRIVILEGES;
```

### 3. Use Environment Variables

Store credentials in environment variables, never in code:

```bash
export DB_PROD_PASSWORD="$(cat ~/.secrets/db_password)"
```

### 4. Network Security

- Use SSL/TLS for database connections
- Restrict database access by IP address
- Use SSH tunnels for remote databases

## Troubleshooting

### Connection Refused

**PostgreSQL/MySQL:**
```
Error: Cannot connect to server. Check if the server is running.
```

Solutions:
- Verify the database server is running
- Check hostname and port are correct
- Ensure firewall allows connections
- Test with `psql` or `mysql` command-line tools

### Authentication Failed

```
Error: Invalid username or password
```

Solutions:
- Verify credentials are correct
- Check user has necessary permissions
- For PostgreSQL, check `pg_hba.conf` allows connections

### SQLite Database Locked

```
Error: SQLite database is locked by another process.
```

Solutions:
- Close other applications using the database
- Wait a moment and try again
- Check file permissions

### ibm_db Installation Issues (macOS)

If `ibm_db` fails to install:

```bash
# Try with no cache
pip install --no-cache-dir ibm_db

# For Apple Silicon, ensure using Python 3.9+
python3 --version
```

## Development

### Running Tests

```bash
pytest tests/
```

### Running with Debug Logging

```bash
export LOG_LEVEL=DEBUG
python -m jdbc_mcp_server
```

### Project Structure

```
jdbc-mcp-server/
├── src/jdbc_mcp_server/
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # Entry point
│   ├── server.py             # FastMCP server and tools
│   ├── config.py             # Configuration management
│   ├── errors.py             # Exception hierarchy
│   ├── utils.py              # Utility functions
│   └── database/
│       ├── base.py           # Abstract database adapter
│       ├── postgresql.py     # PostgreSQL adapter
│       ├── mysql.py          # MySQL adapter
│       ├── sqlite.py         # SQLite adapter
│       └── db2.py            # DB2 adapter
└── tests/                    # Test suite
```

## MVP Status

### Currently Supported (v0.1.0)
- ✅ PostgreSQL
- ✅ MySQL
- ✅ SQLite
- ✅ DB2 iSeries
- ✅ Read-only queries
- ✅ Connection pooling
- ✅ Schema inspection
- ✅ Parameterized queries
- ✅ MCP tools, resources, and prompts

### Coming Soon
- 🔜 Write operations (opt-in)
- 🔜 Transaction support
- 🔜 Query caching
- 🔜 Stored procedure execution

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues, questions, or contributions:
- GitHub Issues: [Create an issue](https://github.com/yourusername/jdbc-mcp-server/issues)
- Documentation: This README

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Implements the [Model Context Protocol](https://modelcontextprotocol.io/)
- Database drivers: psycopg2, mysql-connector-python, ibm_db
