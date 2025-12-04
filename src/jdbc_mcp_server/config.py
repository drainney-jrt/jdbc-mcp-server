"""
Configuration management for the JDBC MCP Server.

Uses Pydantic for validation and supports multiple credential sources:
1. Environment variables (highest priority)
2. Configuration file
3. Inline connection strings (lowest priority)
"""

import os
from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field, SecretStr, validator


class DatabaseConfig(BaseModel):
    """Configuration for a single database connection."""

    type: Literal["postgresql", "mysql", "sqlite", "db2"]
    connection_string: str
    read_only: bool = True
    pool_size: int = Field(default=5, ge=1, le=20)
    pool_timeout: int = Field(default=30, ge=5, le=300)

    class Config:
        """Pydantic configuration."""

        extra = "forbid"  # Don't allow unknown fields


class ServerConfig(BaseModel):
    """Complete server configuration with multiple databases."""

    databases: Dict[str, DatabaseConfig]

    @validator('databases')
    def at_least_one_database(cls, v):
        """Ensure at least one database is configured."""
        if not v:
            raise ValueError("At least one database must be configured")
        return v

    @validator('databases')
    def validate_connection_strings(cls, v):
        """Validate connection string format for each database."""
        for name, config in v.items():
            if not config.connection_string:
                raise ValueError(f"Database '{name}' missing connection string")
        return v

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


def load_config_from_env() -> ServerConfig:
    """
    Load database configuration from environment variables.

    Expected format:
        DB_<NAME>_TYPE=postgresql
        DB_<NAME>_HOST=localhost
        DB_<NAME>_PORT=5432
        DB_<NAME>_DATABASE=mydb
        DB_<NAME>_USERNAME=user
        DB_<NAME>_PASSWORD=pass
        DB_<NAME>_READ_ONLY=true
        DB_<NAME>_POOL_SIZE=10

    Or alternatively:
        DB_<NAME>_CONNECTION_STRING=postgresql://user:pass@localhost:5432/mydb

    Example:
        DB_POSTGRES_TYPE=postgresql
        DB_POSTGRES_HOST=localhost
        DB_POSTGRES_PORT=5432
        ...
    """
    databases = {}

    # Find all database configurations in environment
    db_prefixes = set()
    for key in os.environ:
        if key.startswith("DB_") and "_" in key[3:]:
            parts = key.split("_", 2)
            if len(parts) >= 2:
                db_prefixes.add(parts[1])

    for prefix in db_prefixes:
        db_type = os.getenv(f"DB_{prefix}_TYPE")
        if not db_type:
            continue

        # Check if connection string is provided directly
        connection_string = os.getenv(f"DB_{prefix}_CONNECTION_STRING")

        if not connection_string:
            # Build connection string from individual components
            host = os.getenv(f"DB_{prefix}_HOST", "localhost")
            port = os.getenv(f"DB_{prefix}_PORT")
            database = os.getenv(f"DB_{prefix}_DATABASE")
            username = os.getenv(f"DB_{prefix}_USERNAME")
            password = os.getenv(f"DB_{prefix}_PASSWORD")

            if db_type == "postgresql":
                port = port or "5432"
                connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            elif db_type == "mysql":
                port = port or "3306"
                connection_string = f"mysql://{username}:{password}@{host}:{port}/{database}"
            elif db_type == "sqlite":
                path = os.getenv(f"DB_{prefix}_PATH", database)
                connection_string = f"sqlite:///{path}"
            elif db_type == "db2":
                port = port or "50000"
                connection_string = f"DATABASE={database};HOSTNAME={host};PORT={port};PROTOCOL=TCPIP;UID={username};PWD={password};"

        read_only = os.getenv(f"DB_{prefix}_READ_ONLY", "true").lower() == "true"
        pool_size = int(os.getenv(f"DB_{prefix}_POOL_SIZE", "5"))

        databases[prefix.lower()] = DatabaseConfig(
            type=db_type,
            connection_string=connection_string,
            read_only=read_only,
            pool_size=pool_size
        )

    if not databases:
        raise ValueError(
            "No database configurations found in environment variables. "
            "Set DB_<NAME>_TYPE and related variables."
        )

    return ServerConfig(databases=databases)


def mask_credentials(connection_string: str) -> str:
    """
    Mask credentials in connection strings for logging.

    Args:
        connection_string: The connection string to mask

    Returns:
        Connection string with password masked
    """
    import re

    # Mask password in URL-style connection strings (postgresql://user:PASS@host/db)
    masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', connection_string)

    # Mask password in DB2-style connection strings (PWD=password;)
    masked = re.sub(r'PWD=([^;]+);', r'PWD=****;', masked, flags=re.IGNORECASE)

    return masked
