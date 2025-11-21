"""Review schemas for request/response validation."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .common import BaseSchema, TimestampMixin


class ReviewStatusEnum(str):
    """Review status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ParticipantRoleEnum(str):
    """Participant role in review."""
    LEAD = "lead"
    REVIEWER = "reviewer"
    OBSERVER = "observer"


# Review Participant schemas
class ReviewParticipantBase(BaseModel):
    """Base review participant schema."""
    user_id: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., pattern="^(lead|reviewer|observer)$")


class ReviewParticipantCreate(ReviewParticipantBase):
    """Schema for adding a review participant."""
    pass


class ReviewParticipantResponse(ReviewParticipantBase, BaseSchema):
    """Response schema for review participant."""
    id: UUID
    review_id: UUID
    approved_at: Optional[datetime] = None


# Review schemas
class ReviewBase(BaseModel):
    """Base review schema."""
    rca_text: Optional[str] = None


class ReviewCreate(ReviewBase):
    """Schema for creating a review."""
    participants: Optional[List[ReviewParticipantCreate]] = None


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""
    rca_text: Optional[str] = None


class ReviewDecision(BaseModel):
    """Schema for review decision (approve/reject)."""
    status: str = Field(..., pattern="^(approved|rejected|changes_requested)$")
    comment: Optional[str] = None


class ReviewResponse(ReviewBase, TimestampMixin, BaseSchema):
    """Response schema for review."""
    id: UUID
    entry_id: UUID
    status: str
    participants: List[ReviewParticipantResponse] = []


class ReviewWithEntryResponse(ReviewResponse):
    """Review response with entry details."""
    entry_title: str
    entry_workflow_state: str
