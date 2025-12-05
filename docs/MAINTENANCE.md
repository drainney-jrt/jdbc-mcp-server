# Maintenance Guide

Guide for maintaining and updating the JDBC MCP Server as database vendors and dependencies evolve.

## Table of Contents

- [Overview](#overview)
- [What Needs Maintenance](#what-needs-maintenance)
- [Update Schedule](#update-schedule)
- [Dependency Management](#dependency-management)
- [Testing Updates](#testing-updates)
- [Automated Maintenance](#automated-maintenance)
- [Database Version Updates](#database-version-updates)
- [Security Updates](#security-updates)
- [Troubleshooting](#troubleshooting)

## Overview

The JDBC MCP Server depends on:
- **Python packages** (database drivers, FastMCP, etc.)
- **Database server software** (PostgreSQL, MySQL, SQLite, DB2)
- **Python runtime** (3.10+)
- **MCP protocol** (Model Context Protocol specification)

**Good News:** Database protocols are extremely stable. Most maintenance is just updating Python packages for bug fixes and security patches.

## What Needs Maintenance

### 1. Database Drivers

| Driver | Package | Update Frequency | Breaking Changes |
|--------|---------|------------------|------------------|
| PostgreSQL | `psycopg2-binary` | Monthly | Rare (years) |
| MySQL | `mysql-connector-python` | Monthly | Rare (years) |
| SQLite | Built into Python | With Python | Never |
| DB2 | `ibm_db` | Quarterly | Rare (years) |

### 2. Core Dependencies

| Package | Purpose | Update Frequency |
|---------|---------|------------------|
| `fastmcp` | MCP server framework | Monthly |
| `pydantic` | Configuration validation | Quarterly |
| `sqlparse` | SQL parsing | Quarterly |

### 3. Database Servers

When your organization upgrades database servers:
- PostgreSQL: Test with new version
- MySQL: Test with new version
- DB2: Test with new version
- SQLite: Usually transparent

**Key Point:** The adapters use standard protocols that remain compatible across versions.

## Update Schedule

### Security Updates: **Immediate**

When a security advisory is published:

```bash
# Check for security vulnerabilities
pip install safety
safety check

# Update vulnerable package
pip install --upgrade package-name

# Test immediately
pytest tests/
python -m jdbc_mcp_server
```

### Minor Updates: **Monthly** (First Monday)

```bash
# Check for outdated packages
pip list --outdated

# Update one at a time
pip install --upgrade psycopg2-binary
pytest tests/  # Test after each update

pip install --upgrade mysql-connector-python
pytest tests/

# Continue for each package...
```

### Major Updates: **Quarterly**

Review all dependencies for major version updates:

```bash
# Review release notes for breaking changes
# Plan testing schedule
# Update in staging environment first
# Full integration testing
# Deploy to production
```

### Database Version Updates: **As Needed**

When database servers are upgraded:

```bash
# Test adapters against new database version
# Document tested versions
# Update compatibility matrix in README
```

## Dependency Management

### Current Strategy

We use **compatible release** (`~=`) for most dependencies:

```toml
dependencies = [
    "fastmcp>=2.0.0",              # Allow any 2.x version
    "pydantic>=2.0.0",             # Allow any 2.x version
    "psycopg2-binary>=2.9.0",      # Allow any 2.9+ version
    "mysql-connector-python>=8.0.0",  # Allow any 8.x+ version
    "ibm_db>=3.2.0",               # Allow any 3.2+ version
    "sqlparse>=0.4.0",             # Allow any 0.4+ version
]
```

### Update Strategies

#### Conservative (Production)

Pin major versions, allow minor/patch:

```toml
dependencies = [
    "fastmcp~=2.13.0",    # Allows 2.13.x only
    "pydantic~=2.12.0",
    ...
]
```

**Pros:** Very stable, predictable
**Cons:** Miss bug fixes, security patches

#### Balanced (Recommended)

Pin major versions, allow minor updates:

```toml
dependencies = [
    "fastmcp>=2.0.0,<3.0.0",    # Any 2.x version
    "pydantic>=2.0.0,<3.0.0",
    ...
]
```

**Pros:** Get bug fixes, reasonably stable
**Cons:** Occasional breaking changes in minor versions

#### Aggressive (Development)

No upper bounds:

```toml
dependencies = [
    "fastmcp>=2.0.0",    # Latest available
    "pydantic>=2.0.0",
    ...
]
```

**Pros:** Always latest features
**Cons:** May break unexpectedly

### Recommended: Balanced Approach

Update `pyproject.toml` to use ranges:

```toml
dependencies = [
    "fastmcp>=2.0.0,<3.0.0",
    "pydantic>=2.0.0,<3.0.0",
    "psycopg2-binary>=2.9.0,<3.0.0",
    "mysql-connector-python>=8.0.0,<10.0.0",
    "ibm_db>=3.2.0,<4.0.0",
    "sqlparse>=0.4.0,<0.6.0",
]
```

## Testing Updates

### Automated Testing (Recommended)

See `.github/workflows/test.yml` for CI/CD setup.

```bash
# Run all tests
pytest tests/ -v

# Run specific adapter tests
pytest tests/test_postgresql.py
pytest tests/test_mysql.py
pytest tests/test_sqlite.py
pytest tests/test_db2.py
```

### Manual Testing Checklist

When updating dependencies, test:

- [ ] **Installation**
  ```bash
  pip install -e ".[dev]"
  ```

- [ ] **Import test**
  ```bash
  python -c "from jdbc_mcp_server.database import PostgreSQLAdapter, MySQLAdapter, SQLiteAdapter, DB2Adapter"
  ```

- [ ] **Server startup**
  ```bash
  python -m jdbc_mcp_server
  ```

- [ ] **Connection tests** (per database)
  ```bash
  # Set env vars for your test database
  export DB_TEST_TYPE=postgresql
  export DB_TEST_HOST=localhost
  export DB_TEST_DATABASE=test
  export DB_TEST_USERNAME=test
  export DB_TEST_PASSWORD=test
  python -m jdbc_mcp_server
  ```

- [ ] **MCP tools**
  - `list_databases()`
  - `test_connection()`
  - `list_tables()`
  - `describe_table()`
  - `execute_query()`
  - `get_sample_data()`

- [ ] **Security features**
  - Read-only mode works
  - SQL injection prevention works
  - Parameterized queries work

### Database Server Testing

When testing against new database versions:

```bash
# PostgreSQL 16 → 17
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=test postgres:17
# Test adapter...

# MySQL 8.0 → 9.0
docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=test mysql:9.0
# Test adapter...

# DB2 (requires license)
# Use IBM Cloud or on-premise instance
```

### Testing Matrix

| Python | PostgreSQL | MySQL | SQLite | DB2 |
|--------|------------|-------|--------|-----|
| 3.10   | 12-17      | 8.0-9.0 | 3.x    | 11.x |
| 3.11   | 12-17      | 8.0-9.0 | 3.x    | 11.x |
| 3.12   | 12-17      | 8.0-9.0 | 3.x    | 11.x |
| 3.13   | 12-17      | 8.0-9.0 | 3.x    | 11.x |

## Automated Maintenance

### GitHub Dependabot (Configured)

Dependabot automatically:
- Checks for dependency updates weekly
- Creates pull requests with updates
- Runs CI tests on PRs
- Alerts for security vulnerabilities

**Configuration:** `.github/dependabot.yml`

**Process:**
1. Dependabot creates PR with update
2. GitHub Actions runs tests automatically
3. Review PR and test results
4. Merge if tests pass
5. Deploy updated version

### GitHub Actions (Configured)

Continuous Integration runs on:
- Every push to main
- Every pull request
- Dependabot PRs

**What it tests:**
- Installation succeeds
- Imports work
- Code quality (mypy, black)
- Unit tests pass (when added)
- Multiple Python versions

**Configuration:** `.github/workflows/test.yml`

### Monitoring

**Set up GitHub notifications:**
1. Go to repository settings
2. Notifications → Watch
3. Select "Custom" → Check "Security alerts"

**Subscribe to driver releases:**
- https://github.com/psycopg/psycopg2/releases
- https://github.com/mysql/mysql-connector-python/releases
- https://github.com/ibmdb/python-ibmdb/releases

## Database Version Updates

### When Database Servers Are Upgraded

**PostgreSQL Example:**

```bash
# 1. Check driver compatibility
# Visit: https://www.psycopg.org/docs/install.html
# psycopg2 supports PostgreSQL 9.6 - 17

# 2. Test against new version
docker run -d -p 5433:5432 -e POSTGRES_PASSWORD=test postgres:17
export DB_TEST_PORT=5433
python -m jdbc_mcp_server

# 3. Run full test suite
pytest tests/

# 4. Update documentation
# Edit README.md: "Tested with PostgreSQL 12-17"
```

**MySQL Example:**

```bash
# 1. Check driver compatibility
pip show mysql-connector-python
# Supports MySQL 5.7, 8.0, 8.1, 8.2, 8.3, 8.4, 9.0

# 2. Test against MySQL 9.0
docker run -d -p 3307:3306 -e MYSQL_ROOT_PASSWORD=test mysql:9.0
export DB_TEST_PORT=3307
python -m jdbc_mcp_server

# 3. Test all features
pytest tests/

# 4. Update docs if needed
```

### Handling Breaking Changes

**Rare, but if they occur:**

1. **Check release notes**
   ```bash
   # Example: psycopg2 3.0 (hypothetical)
   pip show psycopg2-binary
   # Read changelog at GitHub
   ```

2. **Test in isolation**
   ```bash
   # Create test environment
   python -m venv test_env
   source test_env/bin/activate
   pip install psycopg2-binary==3.0.0
   # Test adapter
   ```

3. **Update adapter code if needed**
   - Check `src/jdbc_mcp_server/database/postgresql.py`
   - Update for new API
   - Add compatibility layer if possible

4. **Update documentation**
   - Document minimum versions
   - Add migration guide if needed

## Security Updates

### Vulnerability Scanning

**Automated (via GitHub):**
- Dependabot security alerts
- Automatic PRs for security fixes

**Manual check:**
```bash
# Install safety
pip install safety

# Check for vulnerabilities
safety check

# Check specific package
safety check --json | jq '.vulnerabilities'
```

### Response Process

1. **Receive alert** (email from GitHub or `safety check`)
2. **Assess severity** (Critical, High, Medium, Low)
3. **Update immediately** for Critical/High:
   ```bash
   pip install --upgrade vulnerable-package
   pytest tests/
   git commit -m "Security: Update vulnerable-package to X.Y.Z"
   git push
   ```
4. **Schedule update** for Medium/Low
5. **Document in CHANGELOG** (if created)

### Security Best Practices

- **Never commit secrets** to repository
- **Use environment variables** for credentials
- **Enable Dependabot** security alerts
- **Review dependencies** quarterly
- **Monitor CVE databases** for your database vendors
- **Keep Python updated** to latest stable version

## Troubleshooting

### Update Breaks Tests

```bash
# Identify which update caused the issue
git log --oneline

# Rollback specific package
pip install package-name==old-version

# Or rollback all changes
git checkout HEAD~1 pyproject.toml
pip install -e .
```

### Dependency Conflicts

```bash
# Check dependency tree
pip install pipdeptree
pipdeptree

# Find conflicts
pipdeptree --warn conflict

# Resolve by pinning versions
# Edit pyproject.toml with specific versions
```

### Database Driver Issues

**psycopg2 installation fails:**
```bash
# Use binary version (already in pyproject.toml)
pip install psycopg2-binary

# Or install system dependencies
# Ubuntu/Debian:
sudo apt-get install libpq-dev

# macOS:
brew install postgresql
```

**mysql-connector-python issues:**
```bash
# Try official Oracle version
pip install mysql-connector-python --force-reinstall

# Alternative: PyMySQL
pip install PyMySQL
# Update mysql.py adapter to use PyMySQL
```

**ibm_db installation fails:**
```bash
# Clear cache
pip install --no-cache-dir ibm_db

# Ensure correct architecture (Apple Silicon)
arch -arm64 pip install ibm_db
```

## Maintenance Log Template

Keep a maintenance log in `CHANGELOG.md`:

```markdown
## [Date] - Dependency Updates

### Updated
- psycopg2-binary: 2.9.9 → 2.9.11
- mysql-connector-python: 8.3.0 → 9.5.0
- fastmcp: 2.13.0 → 2.13.3

### Tested
- PostgreSQL: 12, 13, 14, 15, 16, 17 ✅
- MySQL: 8.0, 8.4, 9.0 ✅
- Python: 3.10, 3.11, 3.12, 3.13 ✅

### Issues
- None

### Notes
- All tests passing
- No breaking changes
- Ready for production
```

## Quick Reference

### Monthly Maintenance (30 minutes)

```bash
# 1. Check for updates
pip list --outdated

# 2. Review Dependabot PRs
# Visit: https://github.com/drainney-jrt/jdbc-mcp-server/pulls

# 3. Update locally
pip install --upgrade package-name
pytest tests/

# 4. Commit if tests pass
git add pyproject.toml
git commit -m "Update dependencies"
git push
```

### Quarterly Review (2 hours)

```bash
# 1. Review all dependencies
pip list

# 2. Check for major updates
# Visit PyPI for each package

# 3. Test with latest database versions
# Use Docker to test

# 4. Update documentation
# Edit README.md with tested versions

# 5. Create maintenance report
# Document in CHANGELOG.md
```

### Security Patch (Immediate)

```bash
# 1. Update vulnerable package
pip install --upgrade vulnerable-package

# 2. Quick test
pytest tests/

# 3. Deploy immediately
git add pyproject.toml
git commit -m "Security: Update vulnerable-package"
git push
```

## Additional Resources

- **Dependabot Documentation**: https://docs.github.com/en/code-security/dependabot
- **Python Packaging Guide**: https://packaging.python.org/
- **Security Advisories**: https://github.com/advisories
- **Database Driver Docs**:
  - psycopg2: https://www.psycopg.org/docs/
  - mysql-connector: https://dev.mysql.com/doc/connector-python/en/
  - ibm_db: https://github.com/ibmdb/python-ibmdb

## Getting Help

- **Issues**: https://github.com/drainney-jrt/jdbc-mcp-server/issues
- **Database Driver Issues**: Check respective GitHub repositories
- **MCP Protocol**: https://modelcontextprotocol.io/

---

**Last Updated:** 2025-12-04
**Maintainer:** See repository contributors
