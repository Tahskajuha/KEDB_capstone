"""Entry schemas for request/response validation."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .common import BaseSchema, TimestampMixin


class SeverityEnum(str):
    """Entry severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class WorkflowStateEnum(str):
    """Entry workflow states."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    RETIRED = "retired"
    MERGED = "merged"


# Symptom schemas
class EntrySymptomBase(BaseModel):
    """Base symptom schema."""
    description: str = Field(..., min_length=1, max_length=1000)
    order_index: int = Field(..., ge=0)


class EntrySymptomCreate(EntrySymptomBase):
    """Schema for creating a symptom."""
    pass


class EntrySymptomResponse(EntrySymptomBase, BaseSchema):
    """Response schema for symptom."""
    id: UUID
    entry_id: UUID


# Incident schemas
class EntryIncidentBase(BaseModel):
    """Base incident schema."""
    incident_id: str = Field(..., min_length=1, max_length=255)
    incident_source: str = Field(..., min_length=1, max_length=100)


class EntryIncidentCreate(EntryIncidentBase):
    """Schema for linking an incident."""
    pass


class EntryIncidentResponse(EntryIncidentBase, BaseSchema):
    """Response schema for incident."""
    id: UUID
    entry_id: UUID


# Entry schemas
class EntryBase(BaseModel):
    """Base entry schema."""
    title: str = Field(..., min_length=3, max_length=500)
    description: str = Field(..., min_length=10)
    severity: str = Field(..., pattern="^(critical|high|medium|low|info)$")
    root_cause: Optional[str] = None


class EntryCreate(EntryBase):
    """Schema for creating an entry."""
    symptoms: Optional[List[EntrySymptomCreate]] = None
    incidents: Optional[List[EntryIncidentCreate]] = None


class EntryUpdate(BaseModel):
    """Schema for updating an entry."""
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    description: Optional[str] = Field(None, min_length=10)
    severity: Optional[str] = Field(None, pattern="^(critical|high|medium|low|info)$")
    root_cause: Optional[str] = None


class EntryResponse(EntryBase, TimestampMixin, BaseSchema):
    """Response schema for entry."""
    id: UUID
    workflow_state: str
    created_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    merged_into_id: Optional[UUID] = None
    
    # Nested relationships
    symptoms: List[EntrySymptomResponse] = []
    incidents: List[EntryIncidentResponse] = []


class EntryListResponse(BaseModel):
    """Response for entry list with minimal data."""
    id: UUID
    title: str
    severity: str
    workflow_state: str
    created_at: datetime
    created_by: str
    
    model_config = BaseSchema.model_config


class EntryFilter(BaseModel):
    """Filter parameters for entry queries."""
    workflow_state: Optional[str] = Field(None, pattern="^(draft|in_review|published|retired|merged)$")
    severity: Optional[str] = Field(None, pattern="^(critical|high|medium|low|info)$")
    created_by: Optional[str] = None
    search: Optional[str] = None
