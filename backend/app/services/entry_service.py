"""Entry service for business logic."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError, WorkflowError
from app.repositories.entry_repo import EntryRepository
from app.schemas.entry import EntryCreate, EntryIncidentCreate, EntrySymptomCreate, EntryUpdate


class EntryService:
    """Service for Entry business logic."""

    VALID_WORKFLOW_TRANSITIONS = {
        "draft": ["in_review", "retired"],
        "in_review": ["draft", "published", "retired"],
        "published": ["retired", "merged"],
        "retired": [],
        "merged": [],
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = EntryRepository(db)

    async def create_entry(self, entry_data: EntryCreate, created_by: str):
        """Create a new entry."""
        data_dict = entry_data.model_dump(exclude={"symptoms", "incidents"})
        data_dict["created_by"] = created_by
        data_dict["workflow_state"] = "draft"

        symptoms = None
        if entry_data.symptoms:
            symptoms = [s.model_dump() for s in entry_data.symptoms]

        entry = await self.repo.create_with_symptoms(data_dict, symptoms)

        if entry_data.incidents:
            for incident in entry_data.incidents:
                await self.repo.add_incident(entry.id, incident.model_dump())

        return await self.repo.get_with_relations(entry.id)

    async def get_entry(self, entry_id: UUID):
        """Get entry by ID with all relations."""
        entry = await self.repo.get_with_relations(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")
        return entry

    async def list_entries(
        self,
        skip: int = 0,
        limit: int = 20,
        workflow_state: Optional[str] = None,
        severity: Optional[str] = None,
        created_by: Optional[str] = None,
    ):
        """List entries with filters."""
        entries = await self.repo.get_multi_with_filters(
            skip=skip,
            limit=limit,
            workflow_state=workflow_state,
            severity=severity,
            created_by=created_by,
        )
        
        filters = {}
        if workflow_state:
            filters["workflow_state"] = workflow_state
        if severity:
            filters["severity"] = severity
        if created_by:
            filters["created_by"] = created_by
            
        total = await self.repo.count(filters)
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": entries,
        }

    async def update_entry(self, entry_id: UUID, entry_data: EntryUpdate):
        """Update entry."""
        entry = await self.repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        if entry.workflow_state not in ["draft", "in_review"]:
            raise WorkflowError(f"Cannot update entry in {entry.workflow_state} state")

        data_dict = entry_data.model_dump(exclude_unset=True)
        updated = await self.repo.update(entry_id, data_dict)
        return await self.repo.get_with_relations(entry_id)

    async def delete_entry(self, entry_id: UUID):
        """Soft delete entry by marking as retired."""
        entry = await self.repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        await self.repo.update_workflow_state(entry_id, "retired")
        return True

    async def add_symptom(self, entry_id: UUID, symptom_data: EntrySymptomCreate):
        """Add symptom to entry."""
        entry = await self.repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        symptom = await self.repo.add_symptom(entry_id, symptom_data.model_dump())
        return symptom

    async def add_incident(self, entry_id: UUID, incident_data: EntryIncidentCreate):
        """Link incident to entry."""
        entry = await self.repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        incident = await self.repo.add_incident(entry_id, incident_data.model_dump())
        return incident

    async def transition_workflow(self, entry_id: UUID, new_state: str, approved_by: Optional[str] = None):
        """Transition entry to new workflow state."""
        entry = await self.repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        current_state = entry.workflow_state
        valid_transitions = self.VALID_WORKFLOW_TRANSITIONS.get(current_state, [])

        if new_state not in valid_transitions:
            raise WorkflowError(
                f"Invalid transition from {current_state} to {new_state}. "
                f"Valid transitions: {', '.join(valid_transitions)}"
            )

        return await self.repo.update_workflow_state(entry_id, new_state, approved_by)
