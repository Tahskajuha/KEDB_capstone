"""Solution schemas for request/response validation."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .common import BaseSchema, TimestampMixin


class SolutionTypeEnum(str):
    """Solution type."""
    WORKAROUND = "workaround"
    RESOLUTION = "resolution"


# Solution Step schemas
class SolutionStepBase(BaseModel):
    """Base solution step schema."""
    order_index: int = Field(..., ge=0)
    action: str = Field(..., min_length=1, description="Action to perform in this step")
    expected_result: Optional[str] = Field(None, description="Expected result after this step")
    command: Optional[str] = Field(None, description="Command to execute")
    rollback_action: Optional[str] = Field(None, description="How to rollback this step")
    rollback_command: Optional[str] = Field(None, description="Command to rollback")
    step_metadata: Optional[dict] = Field(None, description="Additional metadata as JSON")


class SolutionStepCreate(SolutionStepBase):
    """Schema for creating a solution step."""
    pass


class SolutionStepUpdate(BaseModel):
    """Schema for updating a solution step."""
    order_index: Optional[int] = Field(None, ge=0)
    action: Optional[str] = Field(None, min_length=1)
    expected_result: Optional[str] = None
    command: Optional[str] = None
    rollback_action: Optional[str] = None
    rollback_command: Optional[str] = None
    step_metadata: Optional[dict] = None


class SolutionStepResponse(SolutionStepBase, BaseSchema):
    """Response schema for solution step."""
    id: UUID
    solution_id: UUID


# Solution schemas
class SolutionBase(BaseModel):
    """Base solution schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    solution_type: str = Field(..., pattern="^(workaround|resolution)$")
    estimated_time_minutes: Optional[int] = Field(None, ge=0)


class SolutionCreate(SolutionBase):
    """Schema for creating a solution."""
    steps: Optional[List[SolutionStepCreate]] = None


class SolutionUpdate(BaseModel):
    """Schema for updating a solution."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    solution_type: Optional[str] = Field(None, pattern="^(workaround|resolution)$")
    estimated_time_minutes: Optional[int] = Field(None, ge=0)


class SolutionResponse(SolutionBase, TimestampMixin, BaseSchema):
    """Response schema for solution."""
    id: UUID
    entry_id: UUID
    steps: List[SolutionStepResponse] = []


class SolutionWithEntryResponse(SolutionResponse):
    """Solution response with entry title."""
    entry_title: str
