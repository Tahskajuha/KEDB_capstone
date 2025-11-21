"""Solution service for business logic."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.repositories.entry_repo import EntryRepository
from app.repositories.solution_repo import SolutionRepository
from app.schemas.solution import SolutionCreate, SolutionStepCreate, SolutionStepUpdate, SolutionUpdate


class SolutionService:
    """Service for Solution business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SolutionRepository(db)
        self.entry_repo = EntryRepository(db)

    async def create_solution(self, entry_id: UUID, solution_data: SolutionCreate, created_by: str):
        """Create solution for an entry."""
        entry = await self.entry_repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        data_dict = solution_data.model_dump(exclude={"steps"})
        data_dict["entry_id"] = entry_id
        data_dict["created_by"] = created_by

        steps = None
        if solution_data.steps:
            steps = [s.model_dump() for s in solution_data.steps]

        solution = await self.repo.create_with_steps(data_dict, steps)
        return await self.repo.get_with_steps(solution.id)

    async def get_solution(self, solution_id: UUID):
        """Get solution by ID with steps."""
        solution = await self.repo.get_with_steps(solution_id)
        if not solution:
            raise NotFoundError(f"Solution {solution_id} not found")
        return solution

    async def get_entry_solutions(self, entry_id: UUID):
        """Get all solutions for an entry."""
        entry = await self.entry_repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        return await self.repo.get_by_entry(entry_id)

    async def update_solution(self, solution_id: UUID, solution_data: SolutionUpdate):
        """Update solution."""
        solution = await self.repo.get(solution_id)
        if not solution:
            raise NotFoundError(f"Solution {solution_id} not found")

        data_dict = solution_data.model_dump(exclude_unset=True)
        updated = await self.repo.update(solution_id, data_dict)
        return await self.repo.get_with_steps(solution_id)

    async def delete_solution(self, solution_id: UUID):
        """Delete solution."""
        solution = await self.repo.get(solution_id)
        if not solution:
            raise NotFoundError(f"Solution {solution_id} not found")

        return await self.repo.delete(solution_id)

    async def add_step(self, solution_id: UUID, step_data: SolutionStepCreate):
        """Add step to solution."""
        solution = await self.repo.get(solution_id)
        if not solution:
            raise NotFoundError(f"Solution {solution_id} not found")

        step = await self.repo.add_step(solution_id, step_data.model_dump())
        return step

    async def update_step(self, step_id: UUID, step_data: SolutionStepUpdate):
        """Update solution step."""
        step = await self.repo.get_step(step_id)
        if not step:
            raise NotFoundError(f"Step {step_id} not found")

        data_dict = step_data.model_dump(exclude_unset=True)
        return await self.repo.update_step(step_id, data_dict)

    async def delete_step(self, step_id: UUID):
        """Delete solution step."""
        step = await self.repo.get_step(step_id)
        if not step:
            raise NotFoundError(f"Step {step_id} not found")

        return await self.repo.delete_step(step_id)
