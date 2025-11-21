"""Tag schemas for request/response validation."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .common import BaseSchema


class TagBase(BaseModel):
    """Base tag schema."""
    name: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class TagCreate(TagBase):
    """Schema for creating a tag."""
    pass


class TagUpdate(BaseModel):
    """Schema for updating a tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class TagResponse(TagBase, BaseSchema):
    """Response schema for tag."""
    id: UUID


class EntryTagCreate(BaseModel):
    """Schema for tagging an entry."""
    tag_id: UUID


class EntryTagResponse(BaseSchema):
    """Response schema for entry-tag relationship."""
    id: UUID
    entry_id: UUID
    tag_id: UUID
    tag: TagResponse
