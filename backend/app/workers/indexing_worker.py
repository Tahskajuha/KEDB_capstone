"""Background worker tasks for indexing."""
import asyncio
from uuid import UUID

from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.services.indexing_service import IndexingService


async def _index_entry_async(entry_id: str):
    """Async task to index an entry."""
    async with AsyncSessionLocal() as session:
        service = IndexingService(session)
        await service.index_entry(UUID(entry_id))
        await session.commit()


async def _index_solution_async(solution_id: str):
    """Async task to index a solution."""
    async with AsyncSessionLocal() as session:
        service = IndexingService(session)
        await service.index_solution(UUID(solution_id))
        await session.commit()


def index_entry_task(entry_id: str):
    """RQ task wrapper for indexing entry."""
    logger.info(f"Starting indexing task for entry {entry_id}")
    try:
        asyncio.run(_index_entry_async(entry_id))
        logger.info(f"Completed indexing task for entry {entry_id}")
    except Exception as e:
        logger.error(f"Failed indexing task for entry {entry_id}: {e}")
        raise


def index_solution_task(solution_id: str):
    """RQ task wrapper for indexing solution."""
    logger.info(f"Starting indexing task for solution {solution_id}")
    try:
        asyncio.run(_index_solution_async(solution_id))
        logger.info(f"Completed indexing task for solution {solution_id}")
    except Exception as e:
        logger.error(f"Failed indexing task for solution {solution_id}: {e}")
        raise
