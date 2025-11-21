"""Solution API endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.solution import (
    SolutionCreate,
    SolutionResponse,
    SolutionStepCreate,
    SolutionStepResponse,
    SolutionStepUpdate,
    SolutionUpdate,
)
from app.services.solution_service import SolutionService

router = APIRouter()


@router.post("/entries/{entry_id}/solutions", response_model=SolutionResponse, status_code=status.HTTP_201_CREATED)
async def create_solution(
    entry_id: UUID,
    solution: SolutionCreate,
    created_by: str = Query(..., description="User ID creating the solution"),
    db: AsyncSession = Depends(get_db),
):
    """Create a solution for an entry."""
    try:
        service = SolutionService(db)
        result = await service.create_solution(entry_id, solution, created_by)
        await db.commit()
        return result
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/entries/{entry_id}/solutions", response_model=list[SolutionResponse])
async def get_entry_solutions(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all solutions for an entry."""
    try:
        service = SolutionService(db)
        return await service.get_entry_solutions(entry_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{solution_id}", response_model=SolutionResponse)
async def get_solution(
    solution_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get solution by ID with steps."""
    try:
        service = SolutionService(db)
        return await service.get_solution(solution_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{solution_id}", response_model=SolutionResponse)
async def update_solution(
    solution_id: UUID,
    solution: SolutionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a solution."""
    try:
        service = SolutionService(db)
        result = await service.update_solution(solution_id, solution)
        await db.commit()
        return result
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{solution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_solution(
    solution_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a solution."""
    try:
        service = SolutionService(db)
        await service.delete_solution(solution_id)
        await db.commit()
        return None
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{solution_id}/steps", response_model=SolutionStepResponse, status_code=status.HTTP_201_CREATED)
async def add_step(
    solution_id: UUID,
    step: SolutionStepCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a step to a solution."""
    try:
        service = SolutionService(db)
        result = await service.add_step(solution_id, step)
        await db.commit()
        return result
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/steps/{step_id}", response_model=SolutionStepResponse)
async def update_step(
    step_id: UUID,
    step: SolutionStepUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a solution step."""
    try:
        service = SolutionService(db)
        result = await service.update_step(step_id, step)
        await db.commit()
        return result
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_step(
    step_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a solution step."""
    try:
        service = SolutionService(db)
        await service.delete_step(step_id)
        await db.commit()
        return None
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
