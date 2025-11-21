"""Review API endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.exceptions import NotFoundError, ValidationError, WorkflowError
from app.schemas.review import (
    ReviewCreate,
    ReviewDecision,
    ReviewParticipantCreate,
    ReviewParticipantResponse,
    ReviewResponse,
)
from app.services.review_service import ReviewService

router = APIRouter()


@router.post("/entries/{entry_id}/review", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    entry_id: UUID,
    review: ReviewCreate,
    created_by: str = Query(..., description="User ID creating the review"),
    db: AsyncSession = Depends(get_db),
):
    """Initiate a review for an entry."""
    try:
        service = ReviewService(db)
        result = await service.create_review(entry_id, review, created_by)
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


@router.get("/entries/{entry_id}/reviews", response_model=list[ReviewResponse])
async def get_entry_reviews(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all reviews for an entry."""
    try:
        service = ReviewService(db)
        return await service.get_entry_reviews(entry_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get review by ID with participants."""
    try:
        service = ReviewService(db)
        return await service.get_review(review_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{review_id}/participants", response_model=ReviewParticipantResponse, status_code=status.HTTP_201_CREATED)
async def add_participant(
    review_id: UUID,
    participant: ReviewParticipantCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a participant to a review."""
    try:
        service = ReviewService(db)
        result = await service.add_participant(review_id, participant)
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


@router.put("/{review_id}/decision", response_model=ReviewResponse)
async def submit_decision(
    review_id: UUID,
    decision: ReviewDecision,
    user_id: str = Query(..., description="User ID submitting the decision"),
    db: AsyncSession = Depends(get_db),
):
    """Submit a review decision (approve/reject/changes_requested)."""
    try:
        service = ReviewService(db)
        result = await service.submit_decision(review_id, decision, user_id)
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
