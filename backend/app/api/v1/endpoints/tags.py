"""Tag API endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.common import PaginatedResponse
from app.schemas.tag import EntryTagCreate, EntryTagResponse, TagCreate, TagResponse, TagUpdate
from app.services.tag_service import TagService

router = APIRouter()


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag: TagCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new tag."""
    try:
        service = TagService(db)
        result = await service.create_tag(tag)
        await db.commit()
        return result
    except ConflictError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=PaginatedResponse)
async def list_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all tags with optional category filter."""
    try:
        service = TagService(db)
        return await service.list_tags(skip=skip, limit=limit, category=category)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get tag by ID."""
    try:
        service = TagService(db)
        return await service.get_tag(tag_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: UUID,
    tag: TagUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a tag."""
    try:
        service = TagService(db)
        result = await service.update_tag(tag_id, tag)
        await db.commit()
        return result
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a tag."""
    try:
        service = TagService(db)
        await service.delete_tag(tag_id)
        await db.commit()
        return None
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/entries/{entry_id}/tags", response_model=EntryTagResponse, status_code=status.HTTP_201_CREATED)
async def tag_entry(
    entry_id: UUID,
    tag_data: EntryTagCreate,
    added_by: str = Query("system", description="User ID adding the tag"),
    db: AsyncSession = Depends(get_db),
):
    """Add a tag to an entry."""
    try:
        service = TagService(db)
        result = await service.tag_entry(entry_id, tag_data.tag_id, added_by)
        await db.commit()
        return result
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/entries/{entry_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def untag_entry(
    entry_id: UUID,
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove a tag from an entry."""
    try:
        service = TagService(db)
        await service.untag_entry(entry_id, tag_id)
        await db.commit()
        return None
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/entries/{entry_id}/tags", response_model=list[EntryTagResponse])
async def get_entry_tags(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all tags for an entry."""
    try:
        service = TagService(db)
        return await service.get_entry_tags(entry_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
