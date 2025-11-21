"""Review repository for database operations."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import Review, ReviewParticipant
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    """Repository for Review model."""

    def __init__(self, db: AsyncSession):
        super().__init__(Review, db)

    async def get_with_participants(self, id: UUID) -> Optional[Review]:
        """Get review with all participants."""
        result = await self.db.execute(
            select(Review)
            .where(Review.id == id)
            .options(selectinload(Review.participants))
        )
        return result.scalar_one_or_none()

    async def get_by_entry(self, entry_id: UUID) -> List[Review]:
        """Get all reviews for an entry."""
        result = await self.db.execute(
            select(Review)
            .where(Review.entry_id == entry_id)
            .options(selectinload(Review.participants))
            .order_by(Review.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_with_participants(
        self, review_data: dict, participants: Optional[List[dict]] = None
    ) -> Review:
        """Create review with participants in one transaction."""
        review = Review(**review_data)
        self.db.add(review)
        await self.db.flush()

        if participants:
            for participant_data in participants:
                participant = ReviewParticipant(review_id=review.id, **participant_data)
                self.db.add(participant)

        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def add_participant(self, review_id: UUID, participant_data: dict) -> ReviewParticipant:
        """Add participant to review."""
        participant = ReviewParticipant(review_id=review_id, **participant_data)
        self.db.add(participant)
        await self.db.flush()
        await self.db.refresh(participant)
        return participant

    async def update_status(self, id: UUID, new_status: str) -> Optional[Review]:
        """Update review status."""
        review = await self.get(id)
        if not review:
            return None

        review.status = new_status
        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def approve_by_participant(self, review_id: UUID, user_id: str) -> Optional[ReviewParticipant]:
        """Mark participant as approved."""
        result = await self.db.execute(
            select(ReviewParticipant)
            .where(ReviewParticipant.review_id == review_id)
            .where(ReviewParticipant.user_id == user_id)
        )
        participant = result.scalar_one_or_none()
        
        if not participant:
            return None

        from datetime import datetime, timezone
        participant.approved_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(participant)
        return participant
