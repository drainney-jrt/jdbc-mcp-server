# Using JDBC MCP Server with Windsurf IDE

Complete guide for integrating the JDBC MCP Server with Windsurf IDE's Cascade AI assistant.

## Table of Contents

- [What is Windsurf IDE?](#what-is-windsurf-ide)
- [Quick Setup](#quick-setup)
- [Configuration](#configuration)
- [Using Cascade with Databases](#using-cascade-with-databases)
- [Advanced Workflows](#advanced-workflows)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## What is Windsurf IDE?

Windsurf is an AI-native IDE by Codeium featuring **Cascade**, an intelligent AI assistant that can:
- Understand your entire codebase
- Make multi-file edits
- Execute commands and tools
- Integrate with external services via MCP (Model Context Protocol)

By adding the JDBC MCP Server to Windsurf, Cascade gains the ability to:
- Query your databases directly
- Understand your database schema
- Correlate database structure with your application code
- Generate database-aware code
- Debug data-related issues

## Quick Setup

### 1. Install the JDBC MCP Server

```bash
cd /path/to/jdbc-mcp-server
pip install -e ".[dev]"
```

### 2. Create Windsurf MCP Configuration

**macOS/Linux:**
```bash
mkdir -p ~/.codeium/windsurf
nano ~/.codeium/windsurf/mcp_config.json
```

**Windows:**
```cmd
mkdir %USERPROFILE%\.codeium\windsurf
notepad %USERPROFILE%\.codeium\windsurf\mcp_config.json
```

### 3. Add Configuration

```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "jdbc_mcp_server"],
      "env": {
        "DB_DEV_TYPE": "sqlite",
        "DB_DEV_PATH": "/path/to/your/database.db",
        "DB_DEV_READ_ONLY": "true"
      }
    }
  }
}
```

### 4. Restart Windsurf

Completely quit and restart Windsurf IDE to load the MCP server.

### 5. Verify in Cascade

Open Cascade and ask:
```
"What databases are available?"
```

Cascade should respond with your configured databases!

## Configuration

### Single Database (SQLite)

Perfect for local development:

```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "jdbc_mcp_server"],
      "env": {
        "DB_LOCAL_TYPE": "sqlite",
        "DB_LOCAL_PATH": "/Users/username/myproject/database.db",
        "DB_LOCAL_READ_ONLY": "true"
      }
    }
  }
}
```

### Single Database (PostgreSQL)

For production database access:

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
        "DB_PROD_DATABASE": "production_db",
        "DB_PROD_USERNAME": "readonly_user",
        "DB_PROD_PASSWORD": "secure_password",
        "DB_PROD_READ_ONLY": "true",
        "DB_PROD_POOL_SIZE": "10"
      }
    }
  }
}
```

### Multiple Databases

Connect to multiple databases simultaneously:

```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "jdbc_mcp_server"],
      "env": {
        "DB_PROD_TYPE": "postgresql",
        "DB_PROD_CONNECTION_STRING": "postgresql://readonly@prod.example.com:5432/production",
        "DB_PROD_READ_ONLY": "true",

        "DB_STAGING_TYPE": "postgresql",
        "DB_STAGING_CONNECTION_STRING": "postgresql://user@staging.example.com:5432/staging",
        "DB_STAGING_READ_ONLY": "false",

        "DB_LOCAL_TYPE": "sqlite",
        "DB_LOCAL_PATH": "/Users/username/myproject/local.db",
        "DB_LOCAL_READ_ONLY": "false",

        "DB_ANALYTICS_TYPE": "mysql",
        "DB_ANALYTICS_HOST": "analytics.example.com",
        "DB_ANALYTICS_PORT": "3306",
        "DB_ANALYTICS_DATABASE": "analytics",
        "DB_ANALYTICS_USERNAME": "analyst",
        "DB_ANALYTICS_PASSWORD": "password",
        "DB_ANALYTICS_READ_ONLY": "true"
      }
    }
  }
}
```

## Using Cascade with Databases

### Database Exploration

**List available databases:**
```
"What databases are configured?"
```

**Explore database structure:**
```
"Show me all tables in the prod database"
"What's the schema of the users table?"
"Describe the orders table structure"
```

**Sample data:**
```
"Show me sample data from the products table"
"Get the first 10 rows from users"
```

### Data Querying

**Simple queries:**
```
"How many users are in the database?"
"Show me the most recent orders"
"Find users created in the last month"
```

**Complex analysis:**
```
"What's the average order value by month?"
"Show me the top 10 customers by revenue"
"Find products that have never been ordered"
```

**Cross-database queries:**
```
"Compare user counts between prod and staging"
"Find data inconsistencies between environments"
```

### Code-Database Integration

**Schema validation:**
```
"Does my User model match the database schema?"
"Check if the users table has all the columns my code expects"
"Find any mismatches between my TypeScript interfaces and the database"
```

**Code generation:**
```
"Generate a Python SQLAlchemy model for the users table"
"Create TypeScript types from the database schema"
"Write a migration to add the new columns I need"
```

**Query building:**
```
"Help me write a query to find inactive users"
"Generate a report query for monthly sales"
"Create a query to find duplicate email addresses"
```

## Advanced Workflows

### Workflow 1: Feature Development with Database Context

**Scenario:** Adding a new feature that requires database changes

```
You: "I need to add a subscription feature to my app. Show me the current users table"

Cascade: [Shows users table schema]

You: "Design a subscription system that integrates with this schema"

Cascade: [Proposes new tables, relationships, and migration plan]

You: "Generate the database migration and update my User model"

Cascade: [Creates migration file and updates model code across multiple files]

You: "Show me sample data to test with"

Cascade: [Generates test data based on schema]
```

### Workflow 2: Debugging Data Issues

**Scenario:** User reports a bug related to missing data

```
You: "User ID 12345 reports their orders aren't showing. Investigate."

Cascade:
- Checks if user exists in database
- Queries their orders
- Checks order status and relationships
- Identifies the issue (e.g., orders in different status than expected)
- Suggests fix

You: "Show me where in the code we filter by order status"

Cascade: [Shows relevant code files and suggests fix]
```

### Workflow 3: Schema Refactoring

**Scenario:** Need to rename a column across the application

```
You: "I want to rename the 'email' column to 'email_address' in the users table"

Cascade:
1. Shows all places in code that reference the column
2. Generates database migration
3. Updates all models, queries, and tests
4. Identifies any config or documentation that needs updating

You: "Apply these changes"

Cascade: [Updates all files simultaneously]
```

### Workflow 4: Performance Optimization

**Scenario:** Query performance issues

```
You: "This query is slow, help me optimize it: [shows query]"

Cascade:
- Analyzes query against actual database schema
- Checks for missing indexes
- Suggests query optimization
- Generates migration for new indexes
- Updates code with optimized query

You: "Compare performance before and after"

Cascade: [Runs both queries and shows results]
```

### Workflow 5: Data Migration Planning

**Scenario:** Moving data between environments

```
You: "I need to migrate user data from staging to prod. What do I need to consider?"

Cascade:
- Compares schemas between environments
- Identifies differences and potential conflicts
- Checks for dependent data (foreign keys)
- Suggests migration order and strategy
- Generates migration scripts

You: "Generate the migration scripts"

Cascade: [Creates scripts with proper error handling]
```

## Best Practices

### Security

1. **Always use read-only mode** for production databases
2. **Store credentials securely** - use environment variables or secret managers
3. **Limit access** - create dedicated read-only database users
4. **Review generated queries** before executing on production data
5. **Use separate configs** for different environments

### Effective Prompts

**Be specific about the database:**
```
✅ "Show me the users table in the prod database"
❌ "Show me the users table"
```

**Provide context:**
```
✅ "Find orders from the last week where status is 'pending' and total > $100"
❌ "Find some orders"
```

**Request explanations:**
```
✅ "Explain this query and suggest optimizations: [query]"
❌ "Fix this query: [query]"
```

### Workflow Tips

1. **Start broad, then narrow:**
   - "What databases are available?"
   - "Show me tables in prod"
   - "Describe the users table"
   - "Show me sample data"

2. **Combine database and code queries:**
   - "Check if my model matches the database schema"
   - "Find all code that queries the orders table"

3. **Use Cascade's multi-file editing:**
   - "Update all models to match the current schema"
   - "Refactor all queries to use the new column name"

4. **Leverage context:**
   - Cascade remembers your database structure
   - Reference tables by name without repeating schema
   - Build on previous queries in the conversation

## Troubleshooting

### MCP Server Not Appearing

**Symptom:** Database tools don't show up in Cascade

**Solutions:**
1. Check config file location:
   ```bash
   # macOS/Linux
   cat ~/.codeium/windsurf/mcp_config.json

   # Windows
   type %USERPROFILE%\.codeium\windsurf\mcp_config.json
   ```

2. Validate JSON syntax:
   ```bash
   python -m json.tool ~/.codeium/windsurf/mcp_config.json
   ```

3. Restart Windsurf **completely** (quit and reopen)

4. Check Windsurf logs:
   - View → Output → Select "MCP" from dropdown
   - Look for initialization errors

### Connection Failures

**Symptom:** "Connection refused" or timeout errors

**Solutions:**
1. Test connection manually:
   ```bash
   # Export the same env vars from config
   export DB_PROD_TYPE=postgresql
   export DB_PROD_HOST=localhost
   # ... etc

   python -m jdbc_mcp_server
   ```

2. Verify database is accessible:
   ```bash
   # PostgreSQL
   psql -h localhost -U username -d database

   # MySQL
   mysql -h localhost -u username -p database
   ```

3. Check firewall/network settings
4. Verify credentials are correct

### Slow Performance

**Symptom:** Queries take a long time

**Solutions:**
1. Reduce pool size in configuration
2. Use `limit` parameter in queries
3. Check database server performance
4. Add indexes for frequently queried columns
5. Use read-only replicas for heavy queries

### Python Environment Issues

**Symptom:** "command not found" or import errors

**Solutions:**
1. Use full Python path in config:
   ```json
   {
     "mcpServers": {
       "database": {
         "command": "/usr/local/bin/python3",
         "args": ["-m", "jdbc_mcp_server"],
         ...
       }
     }
   }
   ```

2. Activate virtual environment in command:
   ```json
   {
     "mcpServers": {
       "database": {
         "command": "/bin/bash",
         "args": ["-c", "source /path/to/venv/bin/activate && python -m jdbc_mcp_server"],
         ...
       }
     }
   }
   ```

3. Install in system Python:
   ```bash
   pip install -e /path/to/jdbc-mcp-server
   ```

### Permission Errors

**Symptom:** "Read-only mode" or "Permission denied" errors

**Solutions:**
1. Check `DB_*_READ_ONLY` setting in config
2. Verify database user permissions
3. For write operations, explicitly set:
   ```json
   "DB_DEV_READ_ONLY": "false"
   ```
4. Create queries with proper authorization context

## Integration Examples

### Example 1: Django Project

```json
{
  "mcpServers": {
    "database": {
      "command": "/path/to/django-project/venv/bin/python",
      "args": ["-m", "jdbc_mcp_server"],
      "env": {
        "DB_LOCAL_TYPE": "postgresql",
        "DB_LOCAL_HOST": "localhost",
        "DB_LOCAL_PORT": "5432",
        "DB_LOCAL_DATABASE": "django_db",
        "DB_LOCAL_USERNAME": "django_user",
        "DB_LOCAL_PASSWORD": "password",
        "DB_LOCAL_READ_ONLY": "true"
      }
    }
  }
}
```

Ask Cascade:
- "Compare my Django models with the actual database schema"
- "Find models that are out of sync with the database"
- "Generate migrations for schema differences"

### Example 2: Node.js/Express Project

```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "jdbc_mcp_server"],
      "env": {
        "DB_APP_TYPE": "mysql",
        "DB_APP_HOST": "localhost",
        "DB_APP_DATABASE": "express_app",
        "DB_APP_USERNAME": "root",
        "DB_APP_PASSWORD": "password",
        "DB_APP_READ_ONLY": "true"
      }
    }
  }
}
```

Ask Cascade:
- "Generate TypeScript interfaces from the database schema"
- "Create Prisma schema from the existing database"
- "Find all SQL queries in my codebase and validate them"

### Example 3: Data Science Project

```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "jdbc_mcp_server"],
      "env": {
        "DB_WAREHOUSE_TYPE": "postgresql",
        "DB_WAREHOUSE_CONNECTION_STRING": "postgresql://analyst@warehouse:5432/analytics",
        "DB_WAREHOUSE_READ_ONLY": "true",

        "DB_CACHE_TYPE": "sqlite",
        "DB_CACHE_PATH": "/tmp/analysis_cache.db",
        "DB_CACHE_READ_ONLY": "false"
      }
    }
  }
}
```

Ask Cascade:
- "Load the last 10,000 user events into a DataFrame"
- "Analyze user retention by cohort"
- "Generate SQL for my analysis and cache results locally"

## Additional Resources

- [Main Usage Guide](USAGE.md) - Complete usage documentation
- [Configuration Guide](CONFIGURATION.md) - Database-specific configurations
- [Examples](EXAMPLES.md) - More query examples
- [Windsurf Documentation](https://docs.codeium.com/windsurf) - Official Windsurf docs
- [MCP Protocol](https://modelcontextprotocol.io/) - MCP specification

## Feedback and Support

- **Issues:** https://github.com/drainney-jrt/jdbc-mcp-server/issues
- **Windsurf Community:** Codeium Discord server
- **Documentation:** This repository's docs/ folder
