# Practical Examples

Real-world examples of using the JDBC MCP Server with Claude.

## Table of Contents

- [Getting Started](#getting-started)
- [Database Exploration](#database-exploration)
- [Data Analysis](#data-analysis)
- [Schema Investigation](#schema-investigation)
- [Parameterized Queries](#parameterized-queries)
- [Cross-Database Queries](#cross-database-queries)
- [Common Use Cases](#common-use-cases)

## Getting Started

### Example 1: First Connection

**User prompt:**
> "Can you connect to my database and tell me what's in it?"

**Claude's actions:**
1. Calls `test_connection("prod")`
2. Calls `list_tables("prod")`
3. Provides summary of database contents

**Response:**
```
Connected to PostgreSQL database 'myapp' (version 15.2)
Found 12 tables:
- users (user accounts)
- orders (customer orders)
- products (product catalog)
- ...
```

### Example 2: Quick Table Preview

**User prompt:**
> "Show me what the users table looks like"

**Claude's actions:**
1. Calls `describe_table("prod", "users")`
2. Calls `get_sample_data("prod", "users", limit=5)`

**Response:**
```
Users Table Schema:
- id (integer, primary key)
- email (varchar, not null)
- created_at (timestamp)
- status (varchar)

Sample data:
| id | email              | created_at          | status |
|----|--------------------|--------------------|---------|
| 1  | alice@example.com  | 2024-01-15 10:30:00 | active |
| 2  | bob@example.com    | 2024-01-16 14:20:00 | active |
...
```

## Database Exploration

### Example 3: Understanding Database Structure

**User prompt:**
> "Help me understand the structure of this database"

**Claude's workflow:**
1. Lists all schemas: `list_schemas("prod")`
2. For each schema, lists tables: `list_tables("prod", schema="public")`
3. Describes key tables: `describe_table("prod", "users")`
4. Identifies relationships from foreign key columns

**Result:**
- ER diagram description
- Table relationship summary
- Key entities and their purposes

### Example 4: Finding Specific Tables

**User prompt:**
> "Which tables contain customer information?"

**Claude's actions:**
1. `list_tables("prod")`
2. Examines table names for patterns
3. `describe_table()` for likely candidates
4. `get_sample_data()` to confirm

**Response:**
```
Found 3 tables with customer data:
1. customers - Main customer records
2. customer_addresses - Shipping/billing addresses
3. customer_preferences - User preferences

Would you like me to explore any of these in detail?
```

## Data Analysis

### Example 5: Counting Records

**User prompt:**
> "How many active users do we have?"

**Claude's query:**
```python
execute_query(
    database="prod",
    query="SELECT COUNT(*) as active_users FROM users WHERE status = %s",
    parameters=["active"]
)
```

**Response:**
```
You have 15,847 active users.
```

### Example 6: Finding Recent Data

**User prompt:**
> "Show me orders from the last 7 days"

**Claude's query (PostgreSQL):**
```sql
SELECT
    order_id,
    customer_email,
    total_amount,
    created_at
FROM orders
WHERE created_at > CURRENT_DATE - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 100
```

**Parameters:** None (using SQL date functions)

### Example 7: Aggregating Data

**User prompt:**
> "What's the average order value by month?"

**Claude's query:**
```sql
SELECT
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as order_count,
    AVG(total_amount) as avg_order_value,
    SUM(total_amount) as total_revenue
FROM orders
WHERE created_at >= %s
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC
```

**Parameters:** `["2024-01-01"]`

## Schema Investigation

### Example 8: Finding Column Details

**User prompt:**
> "What columns are in the products table and what type of data do they store?"

**Claude's action:**
```python
describe_table("prod", "products")
```

**Response:**
```
Products table has 8 columns:

1. id (integer, primary key)
   - Unique product identifier

2. sku (varchar(50), not null)
   - Stock Keeping Unit code

3. name (varchar(255), not null)
   - Product name

4. description (text, nullable)
   - Detailed product description

5. price (decimal(10,2), not null)
   - Product price in USD

6. category_id (integer, nullable)
   - Foreign key to categories table

7. stock_quantity (integer, default: 0)
   - Available inventory

8. created_at (timestamp, default: CURRENT_TIMESTAMP)
   - When product was added
```

### Example 9: Identifying Relationships

**User prompt:**
> "What tables are related to the orders table?"

**Claude's analysis:**
1. Describes orders table
2. Identifies foreign key columns (customer_id, product_id, etc.)
3. Checks those referenced tables exist
4. Describes the relationships

**Response:**
```
The orders table has relationships with:

1. customers (via customer_id)
   - Many orders → One customer

2. order_items (via order_id)
   - One order → Many order items

3. shipping_addresses (via shipping_address_id)
   - Many orders → One address

4. payment_methods (via payment_method_id)
   - Many orders → One payment method
```

## Parameterized Queries

### Example 10: Safe User Search

**User prompt:**
> "Find users with email containing 'gmail.com' created after January 1, 2024"

**Bad approach (SQL Injection risk):**
```sql
-- NEVER DO THIS
SELECT * FROM users WHERE email LIKE '%gmail.com%' AND created_at > '2024-01-01'
```

**Good approach (Parameterized):**
```python
# PostgreSQL
execute_query(
    database="prod",
    query="SELECT * FROM users WHERE email LIKE %s AND created_at > %s",
    parameters=["%gmail.com%", "2024-01-01"],
    limit=50
)
```

### Example 11: Multiple Parameters

**User prompt:**
> "Show me products in the 'Electronics' category priced between $100 and $500"

**MySQL query:**
```python
execute_query(
    database="prod",
    query="""
        SELECT p.name, p.price, c.name as category
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE c.name = %s AND p.price BETWEEN %s AND %s
        ORDER BY p.price
    """,
    parameters=["Electronics", 100, 500],
    limit=100
)
```

### Example 12: IN Clause with Parameters

**User prompt:**
> "Show me orders with status 'pending', 'processing', or 'shipped'"

**PostgreSQL query:**
```python
execute_query(
    database="prod",
    query="SELECT * FROM orders WHERE status = ANY(%s)",
    parameters=[["pending", "processing", "shipped"]],
    limit=100
)
```

**SQLite/MySQL alternative:**
```python
# Build IN clause with multiple parameters
execute_query(
    database="prod",
    query="SELECT * FROM orders WHERE status IN (%s, %s, %s)",
    parameters=["pending", "processing", "shipped"],
    limit=100
)
```

## Cross-Database Queries

### Example 13: Comparing Data Across Environments

**User prompt:**
> "Compare the users table structure between production and staging"

**Claude's actions:**
```python
# Get production schema
prod_schema = describe_table("prod", "users")

# Get staging schema
staging_schema = describe_table("staging", "users")

# Compare and report differences
```

**Response:**
```
Schema differences found:

Production has these columns that staging doesn't:
- last_login_ip (varchar)
- email_verified_at (timestamp)

Staging has these columns that production doesn't:
- beta_features_enabled (boolean)

Different types:
- created_at: Production uses 'timestamp', Staging uses 'datetime'
```

### Example 14: Data Validation

**User prompt:**
> "Check if all product IDs in the staging orders table exist in the production products table"

**Approach:**
1. Get distinct product_ids from staging orders
2. Get all product_ids from production products
3. Find IDs in staging but not in production

### Example 15: Copying Reference Data

**User prompt (read-only mode):**
> "Show me the categories from production so I can recreate them in staging"

**Claude's action:**
```python
execute_query(
    database="prod",
    query="SELECT id, name, description, display_order FROM categories ORDER BY display_order"
)
```

**Response provides SQL INSERTs:**
```sql
-- Copy this to staging database:
INSERT INTO categories (id, name, description, display_order) VALUES
(1, 'Electronics', 'Electronic devices', 1),
(2, 'Clothing', 'Apparel and accessories', 2),
(3, 'Books', 'Books and magazines', 3);
```

## Common Use Cases

### Example 16: Debugging Application Issues

**User prompt:**
> "Why isn't user ID 12345 seeing their recent order?"

**Claude's investigation:**
```python
# 1. Check user exists
execute_query("prod", "SELECT * FROM users WHERE id = %s", [12345])

# 2. Check user's orders
execute_query("prod",
    "SELECT * FROM orders WHERE customer_id = %s ORDER BY created_at DESC",
    [12345],
    limit=10
)

# 3. Check order status
execute_query("prod",
    "SELECT o.*, os.name as status_name FROM orders o "
    "JOIN order_statuses os ON o.status_id = os.id "
    "WHERE o.customer_id = %s",
    [12345]
)
```

### Example 17: Performance Analysis

**User prompt:**
> "Which products have never been ordered?"

**Claude's query:**
```sql
SELECT p.id, p.name, p.sku
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
WHERE oi.product_id IS NULL
ORDER BY p.created_at DESC
LIMIT 100
```

### Example 18: Data Quality Checks

**User prompt:**
> "Find any users with invalid email addresses"

**Claude's query (PostgreSQL):**
```sql
SELECT id, email, created_at
FROM users
WHERE email NOT SIMILAR TO '%_@%_._%'
   OR email LIKE '%@localhost%'
   OR email LIKE '%@example.com'
LIMIT 100
```

### Example 19: Reporting

**User prompt:**
> "Create a sales summary for Q1 2024"

**Claude's query:**
```sql
SELECT
    DATE_TRUNC('week', o.created_at) as week,
    COUNT(DISTINCT o.id) as order_count,
    COUNT(DISTINCT o.customer_id) as unique_customers,
    SUM(o.total_amount) as revenue,
    AVG(o.total_amount) as avg_order_value
FROM orders o
WHERE o.created_at BETWEEN %s AND %s
    AND o.status = %s
GROUP BY DATE_TRUNC('week', o.created_at)
ORDER BY week
```

**Parameters:** `["2024-01-01", "2024-03-31", "completed"]`

### Example 20: Migration Planning

**User prompt:**
> "I need to migrate user data to a new system. What's in the users table and what depends on it?"

**Claude's comprehensive analysis:**

1. **User table schema:**
```python
describe_table("prod", "users")
```

2. **Row count:**
```sql
SELECT COUNT(*) FROM users
```

3. **Find dependent tables:**
```sql
-- Check what references users table
SELECT * FROM orders WHERE customer_id = 1 LIMIT 1
SELECT * FROM user_preferences WHERE user_id = 1 LIMIT 1
SELECT * FROM user_addresses WHERE user_id = 1 LIMIT 1
```

4. **Sample data for testing:**
```python
get_sample_data("prod", "users", limit=10)
```

**Result:** Complete migration plan with:
- Schema definition
- Data dependencies
- Sample data for validation
- Recommended migration order

## Tips for Effective Use

### Ask Progressive Questions

Start broad, then narrow down:
1. "What's in this database?"
2. "Tell me about the users table"
3. "Show me active users created this month"
4. "What's the average age of active users created this month?"

### Use Natural Language

Claude understands context:
- "Show me the most recent orders"
- "Which products aren't selling?"
- "Find duplicate emails"
- "What tables are biggest?"

### Leverage Claude's Analysis

Claude can:
- Suggest optimizations
- Identify data quality issues
- Explain query results
- Recommend indexes
- Detect patterns and anomalies

### Safety First

Always:
- Use read-only mode for exploration
- Verify queries before execution on production
- Use parameterized queries
- Test on staging first
- Limit result sets

## Next Steps

- Review [USAGE.md](USAGE.md) for detailed tool documentation
- Check [CONFIGURATION.md](CONFIGURATION.md) for setup instructions
- See main [README.md](../README.md) for security best practices
