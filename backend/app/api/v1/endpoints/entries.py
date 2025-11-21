"""Entry API endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.exceptions import NotFoundError, ValidationError, WorkflowError
from app.schemas.entry import (
    EntryCreate,
    EntryFilter,
    EntryIncidentCreate,
    EntryIncidentResponse,
    EntryListResponse,
    EntryResponse,
    EntrySymptomCreate,
    EntrySymptomResponse,
    EntryUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services.entry_service import EntryService

router = APIRouter()


@router.post("/", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    entry: EntryCreate,
    created_by: str = Query(..., description="User ID creating the entry"),
    db: AsyncSession = Depends(get_db),
):
    """Create a new KEDB entry."""
    try:
        service = EntryService(db)
        result = await service.create_entry(entry, created_by)
        await db.commit()
        return result
    except ValidationError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/")
async def list_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    workflow_state: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    created_by: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List entries with filters and pagination."""
    try:
        service = EntryService(db)
        result = await service.list_entries(
            skip=skip,
            limit=limit,
            workflow_state=workflow_state,
            severity=severity,
            created_by=created_by,
        )
        # Convert Entry models to dict for serialization
        result["items"] = [
            {
                "id": entry.id,
                "title": entry.title,
                "severity": entry.severity,
                "workflow_state": entry.workflow_state,
                "created_at": entry.created_at,
                "created_by": entry.created_by
            }
            for entry in result["items"]
        ]
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{entry_id}", response_model=EntryResponse)
async def get_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get entry by ID with all related data."""
    try:
        service = EntryService(db)
        return await service.get_entry(entry_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{entry_id}", response_model=EntryResponse)
async def update_entry(
    entry_id: UUID,
    entry: EntryUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an entry."""
    try:
        service = EntryService(db)
        result = await service.update_entry(entry_id, entry)
        await db.commit()
        return result
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except WorkflowError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete an entry (mark as retired)."""
    try:
        service = EntryService(db)
        await service.delete_entry(entry_id)
        await db.commit()
        return None
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{entry_id}/symptoms", response_model=EntrySymptomResponse, status_code=status.HTTP_201_CREATED)
async def add_symptom(
    entry_id: UUID,
    symptom: EntrySymptomCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a symptom to an entry."""
    try:
        service = EntryService(db)
        result = await service.add_symptom(entry_id, symptom)
        await db.commit()
        return result
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{entry_id}/incidents", response_model=EntryIncidentResponse, status_code=status.HTTP_201_CREATED)
async def add_incident(
    entry_id: UUID,
    incident: EntryIncidentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Link an incident to an entry."""
    try:
        service = EntryService(db)
        result = await service.add_incident(entry_id, incident)
        await db.commit()
        return result
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
