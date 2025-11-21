"""Tag repository for database operations."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import EntryTag, Tag
from app.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    """Repository for Tag model."""

    def __init__(self, db: AsyncSession):
        super().__init__(Tag, db)

    async def get_by_name(self, name: str) -> Optional[Tag]:
        """Get tag by name."""
        result = await self.db.execute(
            select(Tag).where(Tag.name == name)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, tag_data: dict) -> Tag:
        """Get existing tag by name or create new one."""
        existing = await self.get_by_name(tag_data["name"])
        if existing:
            return existing
        
        return await self.create(tag_data)

    async def get_by_category(self, category: str) -> List[Tag]:
        """Get all tags in a category."""
        result = await self.db.execute(
            select(Tag)
            .where(Tag.category == category)
            .order_by(Tag.name)
        )
        return list(result.scalars().all())


class EntryTagRepository:
    """Repository for EntryTag relationship."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_tag_to_entry(self, entry_id: UUID, tag_id: UUID, added_by: str = "system") -> EntryTag:
        """Add tag to entry."""
        entry_tag = EntryTag(entry_id=entry_id, tag_id=tag_id, added_by=added_by)
        self.db.add(entry_tag)
        await self.db.flush()
        await self.db.refresh(entry_tag)
        return entry_tag

    async def remove_tag_from_entry(self, entry_id: UUID, tag_id: UUID) -> bool:
        """Remove tag from entry."""
        result = await self.db.execute(
            select(EntryTag)
            .where(EntryTag.entry_id == entry_id)
            .where(EntryTag.tag_id == tag_id)
        )
        entry_tag = result.scalar_one_or_none()
        
        if not entry_tag:
            return False
        
        await self.db.delete(entry_tag)
        await self.db.flush()
        return True

    async def get_entry_tags(self, entry_id: UUID) -> List[EntryTag]:
        """Get all tags for an entry."""
        from sqlalchemy.orm import selectinload
        
        result = await self.db.execute(
            select(EntryTag)
            .where(EntryTag.entry_id == entry_id)
            .options(selectinload(EntryTag.tag))
        )
        return list(result.scalars().all())
