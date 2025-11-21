"""Tests for entry CRUD operations."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.mark.asyncio
async def test_create_entry(async_client: AsyncClient):
    """Test creating a new entry."""
    payload = {
        "title": "Database Connection Timeout",
        "description": "Application fails to connect to database after deployment to production environment",
        "severity": "critical",
        "environment": "production",
        "symptoms": [
            {
                "description": "Connection timeout after 30 seconds",
                "order_index": 0
            },
            {
                "description": "Error: ETIMEDOUT connecting to postgres:5432",
                "order_index": 1
            }
        ]
    }

    response = await async_client.post(
        "/api/v1/entries/?created_by=test_user",
        json=payload
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["severity"] == "critical"
    assert data["workflow_state"] == "draft"
    assert len(data["symptoms"]) == 2


@pytest.mark.asyncio
async def test_list_entries(async_client: AsyncClient):
    """Test listing entries."""
    # Create a few entries first
    for i in range(3):
        await async_client.post(
            "/api/v1/entries/?created_by=test_user",
            json={
                "title": f"Test Entry {i}",
                "description": f"Description for entry {i}",
                "severity": "medium"
            }
        )

    response = await async_client.get("/api/v1/entries/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3


@pytest.mark.asyncio
async def test_get_entry(async_client: AsyncClient):
    """Test getting a single entry."""
    # Create an entry
    create_response = await async_client.post(
        "/api/v1/entries/?created_by=test_user",
        json={
            "title": "Test Entry",
            "description": "Test description",
            "severity": "high"
        }
    )
    entry_id = create_response.json()["id"]

    # Get the entry
    response = await async_client.get(f"/api/v1/entries/{entry_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == entry_id
    assert data["title"] == "Test Entry"


@pytest.mark.asyncio
async def test_update_entry(async_client: AsyncClient):
    """Test updating an entry."""
    # Create an entry
    create_response = await async_client.post(
        "/api/v1/entries/?created_by=test_user",
        json={
            "title": "Original Title",
            "description": "Original description",
            "severity": "low"
        }
    )
    entry_id = create_response.json()["id"]

    # Update the entry
    response = await async_client.put(
        f"/api/v1/entries/{entry_id}",
        json={
            "title": "Updated Title",
            "severity": "high"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["severity"] == "high"


@pytest.mark.asyncio
async def test_delete_entry(async_client: AsyncClient):
    """Test soft deleting an entry."""
    # Create an entry
    create_response = await async_client.post(
        "/api/v1/entries/?created_by=test_user",
        json={
            "title": "To Be Deleted",
            "description": "This entry will be deleted",
            "severity": "info"
        }
    )
    entry_id = create_response.json()["id"]

    # Delete the entry
    response = await async_client.delete(f"/api/v1/entries/{entry_id}")
    
    assert response.status_code == 204

    # Verify entry is marked as retired
    get_response = await async_client.get(f"/api/v1/entries/{entry_id}")
    assert get_response.json()["workflow_state"] == "retired"


@pytest.mark.asyncio
async def test_filter_entries_by_severity(async_client: AsyncClient):
    """Test filtering entries by severity."""
    # Create entries with different severities
    await async_client.post(
        "/api/v1/entries/?created_by=test_user",
        json={"title": "Critical", "description": "Desc", "severity": "critical"}
    )
    await async_client.post(
        "/api/v1/entries/?created_by=test_user",
        json={"title": "Low", "description": "Desc", "severity": "low"}
    )

    # Filter by critical
    response = await async_client.get("/api/v1/entries/?severity=critical")
    
    assert response.status_code == 200
    data = response.json()
    assert all(item["severity"] == "critical" for item in data["items"])


@pytest.mark.asyncio
async def test_add_symptom_to_entry(async_client: AsyncClient):
    """Test adding a symptom to an entry."""
    # Create an entry
    create_response = await async_client.post(
        "/api/v1/entries/?created_by=test_user",
        json={
            "title": "Entry for Symptoms",
            "description": "Testing symptom addition",
            "severity": "medium"
        }
    )
    entry_id = create_response.json()["id"]

    # Add a symptom
    response = await async_client.post(
        f"/api/v1/entries/{entry_id}/symptoms",
        json={
            "description": "New symptom observed",
            "order_index": 0
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "New symptom observed"
    assert data["entry_id"] == entry_id
