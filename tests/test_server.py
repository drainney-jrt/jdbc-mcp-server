
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from jdbc_mcp_server.server import mcp
from jdbc_mcp_server import server

@pytest_asyncio.fixture
async def client():
    """Fixture to create a test client."""
    async with AsyncClient(app=mcp, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_adapter():
    """Fixture to create a mock database adapter."""
    adapter = MagicMock()
    adapter.quote_identifier = lambda x: f'"{x}"'
    adapter.execute_query = AsyncMock(return_value=[])
    return adapter

@pytest.mark.asyncio
async def test_get_sample_data_sql_injection_attempt(client, mock_adapter):
    """
    Test that get_sample_data properly quotes identifiers to prevent SQL injection.
    """
    table_name = 'users; DROP TABLE users; --'
    
    with patch.dict(server.adapters, {'test_db': mock_adapter}, clear=True):
        response = await client.post("/tool/get_sample_data", json={
            "database": "test_db",
            "table": table_name,
            "schema": None,
            "limit": 10
        })

    assert response.status_code == 200
    # Check that execute_query was called with a properly quoted query
    expected_query = f'SELECT * FROM "{table_name}" LIMIT %s'
    mock_adapter.execute_query.assert_called_once()
    call_args = mock_adapter.execute_query.call_args
    assert call_args[0][0] == expected_query
    assert call_args[0][1] == (10,)

@pytest.mark.asyncio
async def test_get_sample_data_with_schema(client, mock_adapter):
    """
    Test get_sample_data with a schema.
    """
    with patch.dict(server.adapters, {'test_db': mock_adapter}, clear=True):
        response = await client.post("/tool/get_sample_data", json={
            "database": "test_db",
            "table": "users",
            "schema": "public",
            "limit": 5
        })

    assert response.status_code == 200
    expected_query = 'SELECT * FROM "public"."users" LIMIT %s'
    mock_adapter.execute_query.assert_called_once_with(expected_query, (5,))

@pytest.mark.asyncio
async def test_get_sample_data_db_not_found(client):
    """
    Test that a validation error is returned if the database is not found.
    """
    with patch.dict(server.adapters, {}, clear=True):
        response = await client.post("/tool/get_sample_data", json={
            "database": "nonexistent",
            "table": "users"
        })
    
    assert response.status_code == 200
    result = response.json()
    assert not result['success']
    assert 'not configured' in result['error']
