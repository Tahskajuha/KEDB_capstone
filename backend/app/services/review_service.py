"""Review service for business logic."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError, WorkflowError
from app.repositories.entry_repo import EntryRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewDecision, ReviewParticipantCreate


class ReviewService:
    """Service for Review business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ReviewRepository(db)
        self.entry_repo = EntryRepository(db)

    async def create_review(self, entry_id: UUID, review_data: ReviewCreate, created_by: str):
        """Create a review for an entry."""
        entry = await self.entry_repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        if entry.workflow_state != "draft":
            raise WorkflowError(f"Entry must be in draft state to create review. Current state: {entry.workflow_state}")

        data_dict = review_data.model_dump(exclude={"participants"})
        data_dict["entry_id"] = entry_id
        data_dict["status"] = "pending"

        participants = None
        if review_data.participants:
            participants = [p.model_dump() for p in review_data.participants]

        review = await self.repo.create_with_participants(data_dict, participants)

        # Transition entry to in_review state
        await self.entry_repo.update_workflow_state(entry_id, "in_review")

        return await self.repo.get_with_participants(review.id)

    async def get_review(self, review_id: UUID):
        """Get review by ID with participants."""
        review = await self.repo.get_with_participants(review_id)
        if not review:
            raise NotFoundError(f"Review {review_id} not found")
        return review

    async def get_entry_reviews(self, entry_id: UUID):
        """Get all reviews for an entry."""
        entry = await self.entry_repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        return await self.repo.get_by_entry(entry_id)

    async def add_participant(self, review_id: UUID, participant_data: ReviewParticipantCreate):
        """Add participant to review."""
        review = await self.repo.get(review_id)
        if not review:
            raise NotFoundError(f"Review {review_id} not found")

        if review.status != "pending":
            raise ValidationError(f"Cannot add participants to {review.status} review")

        return await self.repo.add_participant(review_id, participant_data.model_dump())

    async def submit_decision(self, review_id: UUID, decision: ReviewDecision, user_id: str):
        """Submit review decision (approve/reject)."""
        review = await self.repo.get_with_participants(review_id)
        if not review:
            raise NotFoundError(f"Review {review_id} not found")

        if review.status != "pending":
            raise ValidationError(f"Review is already {review.status}")

        # Check if user is a participant
        participant = None
        for p in review.participants:
            if p.user_id == user_id:
                participant = p
                break

        if not participant:
            raise ValidationError(f"User {user_id} is not a participant in this review")

        # Update review status
        await self.repo.update_status(review_id, decision.status)

        # Mark participant as approved if decision is approved
        if decision.status == "approved":
            await self.repo.approve_by_participant(review_id, user_id)

        # Update entry workflow state based on decision
        entry = await self.entry_repo.get(review.entry_id)
        if decision.status == "approved":
            await self.entry_repo.update_workflow_state(review.entry_id, "published", user_id)
        elif decision.status == "rejected":
            await self.entry_repo.update_workflow_state(review.entry_id, "draft")
        elif decision.status == "changes_requested":
            await self.entry_repo.update_workflow_state(review.entry_id, "draft")

        return await self.repo.get_with_participants(review_id)
