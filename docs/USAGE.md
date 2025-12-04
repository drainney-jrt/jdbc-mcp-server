# JDBC MCP Server Usage Guide

This guide provides detailed instructions for using the JDBC MCP Server with Claude Code and Claude Desktop.

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Using with Claude Code](#using-with-claude-code)
- [Using with Claude Desktop](#using-with-claude-desktop)
- [Available Tools](#available-tools)
- [Troubleshooting](#troubleshooting)

## Quick Start

1. **Install the server:**
   ```bash
   cd /Users/dave/claude-projects/jdbc-mcp-server
   pip install -e ".[dev]"
   ```

2. **Configure your database connection** (see [CONFIGURATION.md](CONFIGURATION.md))

3. **Add to Claude Code or Claude Desktop** configuration

4. **Start using database tools** in your Claude conversations!

## Installation

### From Source

```bash
# Clone or navigate to the project
cd /Users/dave/claude-projects/jdbc-mcp-server

# Install with development dependencies
pip install -e ".[dev]"

# Or install without dev dependencies
pip install -e .
```

### Database Drivers

All required database drivers are installed automatically:
- **PostgreSQL**: `psycopg2-binary`
- **MySQL**: `mysql-connector-python`
- **SQLite**: Built into Python
- **DB2**: `ibm_db`

## Configuration

The server uses environment variables to configure database connections. See [CONFIGURATION.md](CONFIGURATION.md) for detailed examples.

### Basic Configuration Pattern

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

## Using with Claude Code

Add the server to your `~/.claude/mcp.json` configuration:

```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "jdbc_mcp_server"],
      "env": {
        "DB_PROD_TYPE": "postgresql",
        "DB_PROD_HOST": "localhost",
        "DB_PROD_PORT": "5432",
        "DB_PROD_DATABASE": "production",
        "DB_PROD_USERNAME": "readonly_user",
        "DB_PROD_PASSWORD": "your_password",
        "DB_PROD_READ_ONLY": "true"
      }
    }
  }
}
```

After updating the configuration:
1. Restart Claude Code
2. The database tools will be available in your conversations
3. Ask Claude to explore your database!

Example prompts:
- "List all tables in the prod database"
- "Show me the schema for the users table"
- "Get sample data from the orders table"
- "Find all customers created in the last month"

## Using with Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "jdbc_mcp_server"],
      "env": {
        "DB_LOCAL_TYPE": "sqlite",
        "DB_LOCAL_PATH": "/Users/yourusername/data/myapp.db",
        "DB_LOCAL_READ_ONLY": "true"
      }
    }
  }
}
```

## Available Tools

### `list_databases()`
Lists all configured database connections.

**Returns**: List of database names and their types.

### `test_connection(database)`
Tests connectivity to a specific database.

**Parameters**:
- `database` (string): Name of the database configuration (e.g., "prod", "local")

**Returns**: Connection status, database type, version, and metadata.

### `list_schemas(database)`
Lists all schemas/databases available (PostgreSQL/MySQL only).

**Parameters**:
- `database` (string): Database name

**Returns**: List of schema names.

### `list_tables(database, schema=None)`
Lists all tables in a database or schema.

**Parameters**:
- `database` (string): Database name
- `schema` (string, optional): Schema name (PostgreSQL/MySQL only)

**Returns**: List of table names.

### `describe_table(database, table, schema=None)`
Gets detailed schema information for a table.

**Parameters**:
- `database` (string): Database name
- `table` (string): Table name
- `schema` (string, optional): Schema name

**Returns**: Column definitions with types, nullability, primary keys, defaults.

### `execute_query(database, query, parameters=None, limit=100)`
Executes a SELECT query with optional parameters.

**Parameters**:
- `database` (string): Database name
- `query` (string): SQL SELECT query
- `parameters` (list, optional): Parameter values for placeholders
- `limit` (int, optional): Maximum rows to return (default: 100)

**Returns**: Query results with columns and rows.

**Important**:
- Only SELECT queries allowed in read-only mode
- Use parameterized queries to prevent SQL injection
- Different databases use different placeholder styles:
  - PostgreSQL: `%(name)s` or `%s`
  - MySQL: `%s`
  - SQLite: `?`
  - DB2: `?`

### `get_sample_data(database, table, schema=None, limit=10)`
Retrieves sample rows from a table.

**Parameters**:
- `database` (string): Database name
- `table` (string): Table name
- `schema` (string, optional): Schema name
- `limit` (int, optional): Number of rows (default: 10)

**Returns**: Sample rows from the table.

## MCP Resources

Access database schemas as resources:

- `db://{database}/schema` - Complete database schema
- `db://{database}/tables/{table}/schema` - Specific table schema

## MCP Prompts

Pre-built workflows for common tasks:

- **explore_database** - Guided database exploration
- **query_with_safety** - Safe parameterized query generation
- **analyze_table_structure** - Table relationship analysis

## Query Examples

### Safe Parameterized Queries

**PostgreSQL**:
```sql
SELECT * FROM users WHERE status = %s AND created_at > %s
```
Parameters: `["active", "2024-01-01"]`

**MySQL**:
```sql
SELECT * FROM orders WHERE customer_id = %s
```
Parameters: `[12345]`

**SQLite/DB2**:
```sql
SELECT * FROM products WHERE category = ? AND price > ?
```
Parameters: `["electronics", 100.00]`

## Security Best Practices

1. **Always use read-only mode** for production databases
2. **Create dedicated read-only database users**
3. **Use parameterized queries** - never concatenate user input
4. **Store credentials in environment variables** - never in code
5. **Use connection strings from secure storage** when possible
6. **Limit network access** to database servers by IP
7. **Use SSL/TLS** for database connections in production

## Troubleshooting

### "Connection pool not initialized"
The database adapter failed to initialize. Check:
- Database server is running
- Credentials are correct
- Network connectivity
- Firewall settings

### "Query contains 'INSERT' but server is in read-only mode"
The server is protecting your data. To enable write operations:
1. Set `DB_<NAME>_READ_ONLY=false`
2. Ensure you understand the risks
3. Consider using a separate write-enabled configuration

### "No database configurations found in environment variables"
No database connections are configured. Make sure you've set the required environment variables with the `DB_<NAME>_` prefix.

### SQLite "database is locked"
Another process is using the database. Close other connections or wait a moment.

### PostgreSQL "connection refused"
- Check PostgreSQL is running: `pg_isready`
- Verify host and port settings
- Check `pg_hba.conf` allows connections

### MySQL "access denied"
- Verify username and password
- Check user has necessary privileges
- Ensure user can connect from your IP address

### DB2 connection issues
- Verify DB2 client libraries are installed
- Check connection string format
- Ensure network connectivity to DB2 server

## Getting Help

- Check [EXAMPLES.md](EXAMPLES.md) for practical examples
- Check [CONFIGURATION.md](CONFIGURATION.md) for database-specific setup
- Review the main [README.md](../README.md) for project overview
- Open an issue on GitHub for bugs or feature requests

## Next Steps

- See [CONFIGURATION.md](CONFIGURATION.md) for database-specific configuration
- See [EXAMPLES.md](EXAMPLES.md) for practical usage examples
- Read the main [README.md](../README.md) for security best practices
