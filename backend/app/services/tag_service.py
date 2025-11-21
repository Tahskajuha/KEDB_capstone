"""Tag service for business logic."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.entry_repo import EntryRepository
from app.repositories.tag_repo import EntryTagRepository, TagRepository
from app.schemas.tag import TagCreate, TagUpdate


class TagService:
    """Service for Tag business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TagRepository(db)
        self.entry_tag_repo = EntryTagRepository(db)
        self.entry_repo = EntryRepository(db)

    async def create_tag(self, tag_data: TagCreate):
        """Create a new tag."""
        existing = await self.repo.get_by_name(tag_data.name)
        if existing:
            raise ConflictError(f"Tag with name '{tag_data.name}' already exists")

        return await self.repo.create(tag_data.model_dump())

    async def get_tag(self, tag_id: UUID):
        """Get tag by ID."""
        tag = await self.repo.get(tag_id)
        if not tag:
            raise NotFoundError(f"Tag {tag_id} not found")
        return tag

    async def list_tags(self, skip: int = 0, limit: int = 100, category: Optional[str] = None):
        """List all tags."""
        if category:
            tags = await self.repo.get_by_category(category)
            return {
                "total": len(tags),
                "skip": 0,
                "limit": len(tags),
                "items": tags,
            }
        
        tags = await self.repo.get_multi(skip=skip, limit=limit)
        total = await self.repo.count()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": tags,
        }

    async def update_tag(self, tag_id: UUID, tag_data: TagUpdate):
        """Update tag."""
        tag = await self.repo.get(tag_id)
        if not tag:
            raise NotFoundError(f"Tag {tag_id} not found")

        if tag_data.name:
            existing = await self.repo.get_by_name(tag_data.name)
            if existing and existing.id != tag_id:
                raise ConflictError(f"Tag with name '{tag_data.name}' already exists")

        data_dict = tag_data.model_dump(exclude_unset=True)
        return await self.repo.update(tag_id, data_dict)

    async def delete_tag(self, tag_id: UUID):
        """Delete tag."""
        tag = await self.repo.get(tag_id)
        if not tag:
            raise NotFoundError(f"Tag {tag_id} not found")

        return await self.repo.delete(tag_id)

    async def tag_entry(self, entry_id: UUID, tag_id: UUID, added_by: str = "system"):
        """Add tag to entry."""
        entry = await self.entry_repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        tag = await self.repo.get(tag_id)
        if not tag:
            raise NotFoundError(f"Tag {tag_id} not found")

        try:
            return await self.entry_tag_repo.add_tag_to_entry(entry_id, tag_id, added_by)
        except Exception as e:
            if "unique" in str(e).lower():
                raise ConflictError(f"Entry {entry_id} is already tagged with {tag_id}")
            raise

    async def untag_entry(self, entry_id: UUID, tag_id: UUID):
        """Remove tag from entry."""
        success = await self.entry_tag_repo.remove_tag_from_entry(entry_id, tag_id)
        if not success:
            raise NotFoundError(f"Entry {entry_id} is not tagged with {tag_id}")
        return True

    async def get_entry_tags(self, entry_id: UUID):
        """Get all tags for an entry."""
        entry = await self.entry_repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        return await self.entry_tag_repo.get_entry_tags(entry_id)
