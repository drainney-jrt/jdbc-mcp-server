# JDBC MCP Server Documentation

Welcome to the JDBC MCP Server documentation. This directory contains comprehensive guides for installing, configuring, and using the server.

## Documentation Index

### 📖 [USAGE.md](USAGE.md)
Complete usage guide covering:
- Installation instructions
- Configuration basics
- Using with Claude Code and Claude Desktop
- Available MCP tools, resources, and prompts
- Query examples
- Security best practices
- Troubleshooting

**Start here** if you're new to the JDBC MCP Server.

### ⚙️ [CONFIGURATION.md](CONFIGURATION.md)
Detailed configuration examples for each database:
- PostgreSQL setup and configuration
- MySQL setup and configuration
- SQLite setup and configuration
- DB2 setup and configuration
- Multiple database configurations
- Connection string formats
- Security and credential management
- SSH tunneling and SSL/TLS

**Use this** when setting up database connections.

### 💡 [EXAMPLES.md](EXAMPLES.md)
Practical examples and common use cases:
- Database exploration workflows
- Data analysis queries
- Schema investigation
- Parameterized query examples
- Cross-database operations
- Real-world scenarios
- Tips and best practices

**Reference this** for inspiration and patterns.

### 🌊 [WINDSURF.md](WINDSURF.md)
Complete guide for Windsurf IDE integration:
- Windsurf IDE and Cascade setup
- Configuration for multiple databases
- Advanced Cascade workflows
- Code-database integration examples
- Best practices for Windsurf users
- Troubleshooting Windsurf-specific issues

**Use this** if you're using Windsurf IDE with Cascade.

### 🔧 [MAINTENANCE.md](MAINTENANCE.md)
Guide for keeping the server updated:
- Dependency update schedule
- Database driver maintenance
- Testing strategy
- Automated updates with Dependabot
- Security patch process
- Troubleshooting updates

**Reference this** for ongoing maintenance and updates.

## Quick Links

- [Main README](../README.md) - Project overview and quick start
- [Source Code](../src/jdbc_mcp_server/) - Implementation details
- [Tests](../tests/) - Test suite

## Getting Started

1. **Install the server:**
   ```bash
   pip install -e ".[dev]"
   ```

2. **Configure your database** - see [CONFIGURATION.md](CONFIGURATION.md)

3. **Add to Claude** - see [USAGE.md](USAGE.md#using-with-claude-code)

4. **Start exploring** - see [EXAMPLES.md](EXAMPLES.md)

## Supported Databases

- ✅ **PostgreSQL** - Full support with connection pooling
- ✅ **MySQL** - Full support with connection pooling
- ✅ **SQLite** - Full support (file-based)
- ✅ **DB2 iSeries** - Full support with connection pooling

## Key Features

- **Read-Only by Default** - Safe database exploration
- **Parameterized Queries** - SQL injection prevention
- **Connection Pooling** - Efficient resource management
- **Multiple Databases** - Connect to multiple databases simultaneously
- **Schema Inspection** - Automatic table and column discovery
- **MCP Protocol** - Native integration with Claude

## Documentation Structure

```
docs/
├── README.md           # This file - documentation index
├── USAGE.md           # Complete usage guide
├── CONFIGURATION.md   # Database configuration examples
├── EXAMPLES.md        # Practical examples
├── WINDSURF.md        # Windsurf IDE integration guide
└── MAINTENANCE.md     # Maintenance and update guide
```

## Need Help?

- **Configuration issues?** See [CONFIGURATION.md](CONFIGURATION.md#troubleshooting-configuration)
- **Usage questions?** See [USAGE.md](USAGE.md#troubleshooting)
- **Looking for examples?** See [EXAMPLES.md](EXAMPLES.md)
- **Security concerns?** See [CONFIGURATION.md](CONFIGURATION.md#security)

## Contributing

Found an issue or have a suggestion? Please open an issue on GitHub or submit a pull request.

## License

MIT License - see [LICENSE](../LICENSE) file for details.
