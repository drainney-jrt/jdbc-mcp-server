# Database Configuration Guide

Detailed configuration examples for each supported database type.

## Table of Contents

- [PostgreSQL](#postgresql)
- [MySQL](#mysql)
- [SQLite](#sqlite)
- [DB2](#db2)
- [Multiple Databases](#multiple-databases)
- [Connection Strings](#connection-strings)
- [Security](#security)

## PostgreSQL

### Environment Variables

```bash
DB_POSTGRES_TYPE=postgresql
DB_POSTGRES_HOST=localhost
DB_POSTGRES_PORT=5432
DB_POSTGRES_DATABASE=myapp
DB_POSTGRES_USERNAME=readonly_user
DB_POSTGRES_PASSWORD=secure_password
DB_POSTGRES_READ_ONLY=true
DB_POSTGRES_POOL_SIZE=10
```

### Claude Code/Desktop Configuration

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

### Connection String Format

```bash
DB_POSTGRES_TYPE=postgresql
DB_POSTGRES_CONNECTION_STRING=postgresql://readonly_user:secure_password@localhost:5432/myapp
DB_POSTGRES_READ_ONLY=true
```

### Creating a Read-Only PostgreSQL User

```sql
-- Create read-only user
CREATE USER readonly_user WITH PASSWORD 'secure_password';

-- Grant connection to database
GRANT CONNECT ON DATABASE myapp TO readonly_user;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO readonly_user;

-- Grant SELECT on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- Grant SELECT on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO readonly_user;

-- Verify permissions
\c myapp readonly_user
SELECT * FROM information_schema.table_privileges
WHERE grantee = 'readonly_user';
```

### SSL/TLS Connection

```bash
DB_POSTGRES_CONNECTION_STRING=postgresql://user:pass@host:5432/db?sslmode=require
```

SSL modes: `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full`

## MySQL

### Environment Variables

```bash
DB_MYSQL_TYPE=mysql
DB_MYSQL_HOST=localhost
DB_MYSQL_PORT=3306
DB_MYSQL_DATABASE=myapp
DB_MYSQL_USERNAME=readonly_user
DB_MYSQL_PASSWORD=secure_password
DB_MYSQL_READ_ONLY=true
DB_MYSQL_POOL_SIZE=10
```

### Claude Code/Desktop Configuration

```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "jdbc_mcp_server"],
      "env": {
        "DB_MYSQL_TYPE": "mysql",
        "DB_MYSQL_HOST": "localhost",
        "DB_MYSQL_PORT": "3306",
        "DB_MYSQL_DATABASE": "myapp",
        "DB_MYSQL_USERNAME": "readonly_user",
        "DB_MYSQL_PASSWORD": "secure_password",
        "DB_MYSQL_READ_ONLY": "true",
        "DB_MYSQL_POOL_SIZE": "10"
      }
    }
  }
}
```

### Connection String Format

```bash
DB_MYSQL_TYPE=mysql
DB_MYSQL_CONNECTION_STRING=mysql://readonly_user:secure_password@localhost:3306/myapp
DB_MYSQL_READ_ONLY=true
```

### Creating a Read-Only MySQL User

```sql
-- Create read-only user
CREATE USER 'readonly_user'@'%' IDENTIFIED BY 'secure_password';

-- Grant SELECT on specific database
GRANT SELECT ON myapp.* TO 'readonly_user'@'%';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify permissions
SHOW GRANTS FOR 'readonly_user'@'%';
```

### Restrict by IP Address

```sql
-- Create user for specific IP
CREATE USER 'readonly_user'@'192.168.1.100' IDENTIFIED BY 'secure_password';
GRANT SELECT ON myapp.* TO 'readonly_user'@'192.168.1.100';
FLUSH PRIVILEGES;
```

## SQLite

### Environment Variables

```bash
DB_SQLITE_TYPE=sqlite
DB_SQLITE_PATH=/path/to/database.db
DB_SQLITE_READ_ONLY=true
```

### Claude Code/Desktop Configuration

```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "jdbc_mcp_server"],
      "env": {
        "DB_SQLITE_TYPE": "sqlite",
        "DB_SQLITE_PATH": "/Users/username/data/myapp.db",
        "DB_SQLITE_READ_ONLY": "true"
      }
    }
  }
}
```

### Connection String Format

```bash
DB_SQLITE_TYPE=sqlite
DB_SQLITE_CONNECTION_STRING=sqlite:////absolute/path/to/database.db
DB_SQLITE_READ_ONLY=true
```

### In-Memory Database (Testing)

```bash
DB_SQLITE_CONNECTION_STRING=sqlite:///:memory:
DB_SQLITE_READ_ONLY=false
```

### Notes

- SQLite paths must be absolute (start with `/`)
- Connection string format: `sqlite:///` followed by path
- No connection pooling needed (file-based)
- Read-only mode prevents writes but doesn't enforce file permissions

## DB2

### Environment Variables

```bash
DB_DB2_TYPE=db2
DB_DB2_HOST=db2server.example.com
DB_DB2_PORT=50000
DB_DB2_DATABASE=SAMPLE
DB_DB2_USERNAME=readonly_user
DB_DB2_PASSWORD=secure_password
DB_DB2_READ_ONLY=true
DB_DB2_POOL_SIZE=5
```

### Claude Code/Desktop Configuration

```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "jdbc_mcp_server"],
      "env": {
        "DB_DB2_TYPE": "db2",
        "DB_DB2_HOST": "db2server.example.com",
        "DB_DB2_PORT": "50000",
        "DB_DB2_DATABASE": "SAMPLE",
        "DB_DB2_USERNAME": "readonly_user",
        "DB_DB2_PASSWORD": "secure_password",
        "DB_DB2_READ_ONLY": "true",
        "DB_DB2_POOL_SIZE": "5"
      }
    }
  }
}
```

### Connection String Format

```bash
DB_DB2_TYPE=db2
DB_DB2_CONNECTION_STRING=DATABASE=SAMPLE;HOSTNAME=db2server.example.com;PORT=50000;PROTOCOL=TCPIP;UID=readonly_user;PWD=secure_password;
DB_DB2_READ_ONLY=true
```

### Creating a Read-Only DB2 User

```sql
-- Create user (via system commands or RACF on iSeries)
-- Grant SELECT privileges
GRANT SELECT ON SCHEMA your_schema TO USER readonly_user;

-- Or grant on specific tables
GRANT SELECT ON your_schema.table_name TO USER readonly_user;
```

### DB2 iSeries Specific

For IBM i (AS/400):
- Default port: 50000 (or 446 for SSL)
- May need to configure DB2 Connect or configure ODBC
- Schema names are typically library names

## Multiple Databases

You can configure multiple databases simultaneously:

### Example: Production, Staging, and Local

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
        "DB_PROD_POOL_SIZE": "10",

        "DB_STAGING_TYPE": "postgresql",
        "DB_STAGING_CONNECTION_STRING": "postgresql://user@staging-server:5432/staging",
        "DB_STAGING_READ_ONLY": "false",
        "DB_STAGING_POOL_SIZE": "5",

        "DB_LOCAL_TYPE": "sqlite",
        "DB_LOCAL_PATH": "/Users/username/data/local.db",
        "DB_LOCAL_READ_ONLY": "false"
      }
    }
  }
}
```

### Mixed Database Types

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
        "DB_POSTGRES_DATABASE": "users",
        "DB_POSTGRES_USERNAME": "reader",
        "DB_POSTGRES_PASSWORD": "pass1",
        "DB_POSTGRES_READ_ONLY": "true",

        "DB_MYSQL_TYPE": "mysql",
        "DB_MYSQL_HOST": "localhost",
        "DB_MYSQL_PORT": "3306",
        "DB_MYSQL_DATABASE": "analytics",
        "DB_MYSQL_USERNAME": "analyst",
        "DB_MYSQL_PASSWORD": "pass2",
        "DB_MYSQL_READ_ONLY": "true",

        "DB_CACHE_TYPE": "sqlite",
        "DB_CACHE_PATH": "/tmp/cache.db",
        "DB_CACHE_READ_ONLY": "false"
      }
    }
  }
}
```

## Connection Strings

### Advantages
- More concise configuration
- Can include additional connection parameters
- Standard URI format

### Format by Database Type

**PostgreSQL:**
```
postgresql://[user[:password]@][host][:port][/database][?param=value&...]
```

**MySQL:**
```
mysql://[user[:password]@][host][:port][/database]
```

**SQLite:**
```
sqlite:///[/absolute/path/to/database.db]
```

**DB2:**
```
DATABASE=name;HOSTNAME=host;PORT=port;PROTOCOL=TCPIP;UID=user;PWD=pass;
```

### Connection String Parameters

**PostgreSQL:**
- `sslmode=require` - Enforce SSL
- `connect_timeout=10` - Connection timeout
- `application_name=mcp_server` - Application name
- `options=-c statement_timeout=30000` - Statement timeout

**MySQL:**
- Additional parameters not commonly used in connection strings
- Configure via environment or connection pool settings

## Security

### Credential Management

**Environment Variables (Development):**
```bash
export DB_PROD_PASSWORD="my_secure_password"
python -m jdbc_mcp_server
```

**Secret Files (Production):**
```bash
export DB_PROD_PASSWORD="$(cat ~/.secrets/db_password)"
```

**Credential Stores:**
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- 1Password CLI

Example with AWS Secrets Manager:
```bash
export DB_PROD_PASSWORD="$(aws secretsmanager get-secret-value --secret-id prod-db-password --query SecretString --output text)"
```

### SSH Tunneling

For remote databases, use SSH tunnels:

```bash
# Create tunnel
ssh -L 5432:localhost:5432 user@remote-server

# Configure as localhost
DB_PROD_HOST=localhost
DB_PROD_PORT=5432
```

### Network Security

- Restrict database server firewall to known IPs
- Use VPN for remote database access
- Enable SSL/TLS for all connections
- Use non-standard ports (security through obscurity)
- Implement connection rate limiting

### Best Practices

1. **Never commit credentials** to version control
2. **Use read-only users** for exploration
3. **Limit connection pool size** to avoid resource exhaustion
4. **Set connection timeouts** to prevent hanging connections
5. **Monitor connection usage** and audit logs
6. **Rotate credentials** regularly
7. **Use least privilege** - grant minimum necessary permissions
8. **Enable audit logging** on database server

## Troubleshooting Configuration

### Test Your Configuration

```bash
# Set environment variables
export DB_TEST_TYPE=postgresql
export DB_TEST_HOST=localhost
export DB_TEST_PORT=5432
export DB_TEST_DATABASE=testdb
export DB_TEST_USERNAME=testuser
export DB_TEST_PASSWORD=testpass
export DB_TEST_READ_ONLY=true

# Run the server
python -m jdbc_mcp_server
```

### Validate Connection String

Use database-specific tools:

**PostgreSQL:**
```bash
psql "postgresql://user:pass@host:5432/database" -c "SELECT 1"
```

**MySQL:**
```bash
mysql -h host -P 3306 -u user -ppass database -e "SELECT 1"
```

**SQLite:**
```bash
sqlite3 /path/to/database.db "SELECT 1"
```

### Common Issues

**"No database configurations found"**
- Check environment variable prefix is `DB_`
- Ensure `DB_<NAME>_TYPE` is set
- Verify variables are exported

**"Invalid connection string"**
- Check format matches database type
- Ensure special characters are properly encoded
- Verify paths are absolute (SQLite)

**"Connection refused"**
- Database server may not be running
- Check host and port settings
- Verify firewall rules
- Test network connectivity

## Next Steps

- See [USAGE.md](USAGE.md) for how to use the configured databases
- See [EXAMPLES.md](EXAMPLES.md) for practical examples
- Review main [README.md](../README.md) for security best practices
