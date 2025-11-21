"""Entry repository for database operations."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entry import Entry, EntryIncident, EntrySymptom
from app.repositories.base import BaseRepository


class EntryRepository(BaseRepository[Entry]):
    """Repository for Entry model."""

    def __init__(self, db: AsyncSession):
        super().__init__(Entry, db)

    async def get_with_relations(self, id: UUID) -> Optional[Entry]:
        """Get entry with all related data (symptoms, incidents, solutions, tags)."""
        result = await self.db.execute(
            select(Entry)
            .where(Entry.id == id)
            .options(
                selectinload(Entry.symptoms),
                selectinload(Entry.incidents),
                selectinload(Entry.solutions),
                selectinload(Entry.tags),
            )
        )
        return result.scalar_one_or_none()

    async def get_multi_with_filters(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        workflow_state: Optional[str] = None,
        severity: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> List[Entry]:
        """Get entries with filters."""
        query = select(Entry)

        if workflow_state:
            query = query.where(Entry.workflow_state == workflow_state)
        if severity:
            query = query.where(Entry.severity == severity)
        if created_by:
            query = query.where(Entry.created_by == created_by)

        query = query.order_by(Entry.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_with_symptoms(
        self, entry_data: dict, symptoms: Optional[List[dict]] = None
    ) -> Entry:
        """Create entry with symptoms in one transaction."""
        entry = Entry(**entry_data)
        self.db.add(entry)
        await self.db.flush()

        if symptoms:
            for symptom_data in symptoms:
                symptom = EntrySymptom(entry_id=entry.id, **symptom_data)
                self.db.add(symptom)

        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def add_symptom(self, entry_id: UUID, symptom_data: dict) -> EntrySymptom:
        """Add symptom to entry."""
        symptom = EntrySymptom(entry_id=entry_id, **symptom_data)
        self.db.add(symptom)
        await self.db.flush()
        await self.db.refresh(symptom)
        return symptom

    async def add_incident(self, entry_id: UUID, incident_data: dict) -> EntryIncident:
        """Link incident to entry."""
        incident = EntryIncident(entry_id=entry_id, **incident_data)
        self.db.add(incident)
        await self.db.flush()
        await self.db.refresh(incident)
        return incident

    async def update_workflow_state(self, id: UUID, new_state: str, approved_by: Optional[str] = None) -> Optional[Entry]:
        """Update entry workflow state."""
        entry = await self.get(id)
        if not entry:
            return None

        entry.workflow_state = new_state
        if approved_by:
            entry.approved_by = approved_by
            from datetime import datetime, timezone
            entry.approved_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(entry)
        return entry
