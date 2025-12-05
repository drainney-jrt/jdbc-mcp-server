import os
import unittest
from unittest.mock import patch

from jdbc_mcp_server.config import load_config_from_env, ServerConfig, DatabaseConfig, mask_credentials

class TestConfig(unittest.TestCase):

    @patch.dict(os.environ, {}, clear=True)
    def test_load_config_from_env_no_vars(self):
        """
        Test that a ValueError is raised if no DB environment variables are set.
        """
        with self.assertRaises(ValueError):
            load_config_from_env()

    @patch.dict(os.environ, {
        "DB_TESTDB_TYPE": "postgresql",
        "DB_TESTDB_HOST": "localhost",
        "DB_TESTDB_PORT": "5432",
        "DB_TESTDB_DATABASE": "test",
        "DB_TESTDB_USERNAME": "user",
        "DB_TESTDB_PASSWORD": "password",
    })
    def test_load_config_from_env_postgres(self):
        """
        Test loading a PostgreSQL configuration.
        """
        config = load_config_from_env()
        self.assertIn("testdb", config.databases)
        db_config = config.databases["testdb"]
        self.assertEqual(db_config.type, "postgresql")
        self.assertEqual(db_config.connection_string, "postgresql://user:password@localhost:5432/test")
        self.assertTrue(db_config.read_only)
        self.assertEqual(db_config.pool_size, 5)

    @patch.dict(os.environ, {
        "DB_SQLITE_TYPE": "sqlite",
        "DB_SQLITE_PATH": "/var/data/test.db",
    })
    def test_load_config_from_env_sqlite(self):
        """
        Test loading a SQLite configuration.
        """
        config = load_config_from_env()
        self.assertIn("sqlite", config.databases)
        db_config = config.databases["sqlite"]
        self.assertEqual(db_config.type, "sqlite")
        self.assertEqual(db_config.connection_string, "sqlite:////var/data/test.db")

    @patch.dict(os.environ, {
        "DB_MYSQL_CONNECTION_STRING": "mysql://user:pass@host:3306/db",
        "DB_MYSQL_TYPE": "mysql",
    })
    def test_load_config_from_env_connection_string(self):
        """
        Test loading a configuration using a direct connection string.
        """
        config = load_config_from_env()
        self.assertIn("mysql", config.databases)
        db_config = config.databases["mysql"]
        self.assertEqual(db_config.type, "mysql")
        self.assertEqual(db_config.connection_string, "mysql://user:pass@host:3306/db")

    def test_mask_credentials_postgres(self):
        """
        Test masking credentials in a PostgreSQL connection string.
        """
        original = "postgresql://user:supersecret@localhost:5432/mydb"
        masked = "postgresql://user:****@localhost:5432/mydb"
        self.assertEqual(mask_credentials(original), masked)

    def test_mask_credentials_db2(self):
        """
        Test masking credentials in a DB2 connection string.
        """
        original = "DATABASE=mydb;HOSTNAME=localhost;PORT=50000;PROTOCOL=TCPIP;UID=user;PWD=supersecret;"
        masked = "DATABASE=mydb;HOSTNAME=localhost;PORT=50000;PROTOCOL=TCPIP;UID=user;PWD=****;"
        self.assertEqual(mask_credentials(original), masked)

if __name__ == "__main__":
    unittest.main()