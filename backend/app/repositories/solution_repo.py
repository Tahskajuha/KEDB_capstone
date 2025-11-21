"""Solution repository for database operations."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.solution import Solution, SolutionStep
from app.repositories.base import BaseRepository


class SolutionRepository(BaseRepository[Solution]):
    """Repository for Solution model."""

    def __init__(self, db: AsyncSession):
        super().__init__(Solution, db)

    async def get_with_steps(self, id: UUID) -> Optional[Solution]:
        """Get solution with all steps."""
        result = await self.db.execute(
            select(Solution)
            .where(Solution.id == id)
            .options(selectinload(Solution.steps))
        )
        return result.scalar_one_or_none()

    async def get_by_entry(self, entry_id: UUID) -> List[Solution]:
        """Get all solutions for an entry."""
        result = await self.db.execute(
            select(Solution)
            .where(Solution.entry_id == entry_id)
            .options(selectinload(Solution.steps))
            .order_by(Solution.created_at)
        )
        return list(result.scalars().all())

    async def create_with_steps(
        self, solution_data: dict, steps: Optional[List[dict]] = None
    ) -> Solution:
        """Create solution with steps in one transaction."""
        solution = Solution(**solution_data)
        self.db.add(solution)
        await self.db.flush()

        if steps:
            for step_data in steps:
                step = SolutionStep(solution_id=solution.id, **step_data)
                self.db.add(step)

        await self.db.flush()
        await self.db.refresh(solution)
        return solution

    async def add_step(self, solution_id: UUID, step_data: dict) -> SolutionStep:
        """Add step to solution."""
        step = SolutionStep(solution_id=solution_id, **step_data)
        self.db.add(step)
        await self.db.flush()
        await self.db.refresh(step)
        return step

    async def get_step(self, step_id: UUID) -> Optional[SolutionStep]:
        """Get single solution step."""
        result = await self.db.execute(
            select(SolutionStep).where(SolutionStep.id == step_id)
        )
        return result.scalar_one_or_none()

    async def update_step(self, step_id: UUID, step_data: dict) -> Optional[SolutionStep]:
        """Update solution step."""
        step = await self.get_step(step_id)
        if not step:
            return None

        for field, value in step_data.items():
            if hasattr(step, field):
                setattr(step, field, value)

        await self.db.flush()
        await self.db.refresh(step)
        return step

    async def delete_step(self, step_id: UUID) -> bool:
        """Delete solution step."""
        step = await self.get_step(step_id)
        if not step:
            return False

        await self.db.delete(step)
        await self.db.flush()
        return True
