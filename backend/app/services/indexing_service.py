"""Indexing service for Meilisearch and vector embeddings."""
import asyncio
from typing import List, Optional
from uuid import UUID

import httpx
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.models.embedding import EntryEmbedding, SolutionEmbedding
from app.models.entry import Entry
from app.models.solution import Solution
from app.repositories.entry_repo import EntryRepository
from app.repositories.solution_repo import SolutionRepository


class IndexingService:
    """Service for indexing entries and solutions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.entry_repo = EntryRepository(db)
        self.solution_repo = SolutionRepository(db)
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.meilisearch_url = str(settings.meilisearch_url)
        self.meilisearch_key = settings.meilisearch_master_key

    async def index_entry(self, entry_id: UUID):
        """Index entry in Meilisearch and generate embeddings."""
        entry = await self.entry_repo.get_with_relations(entry_id)
        if not entry:
            logger.warning(f"Entry {entry_id} not found for indexing")
            return

        # Index in Meilisearch
        await self._index_entry_meilisearch(entry)

        # Generate and store embeddings
        if self.openai_client:
            await self._generate_entry_embedding(entry)

    async def index_solution(self, solution_id: UUID):
        """Index solution and generate embeddings."""
        solution = await self.solution_repo.get_with_steps(solution_id)
        if not solution:
            logger.warning(f"Solution {solution_id} not found for indexing")
            return

        # Generate and store embeddings
        if self.openai_client:
            await self._generate_solution_embedding(solution)

    async def _index_entry_meilisearch(self, entry: Entry):
        """Index entry in Meilisearch."""
        try:
            # Prepare entry document
            symptoms_text = " ".join([s.description for s in entry.symptoms])
            
            document = {
                "id": str(entry.id),
                "title": entry.title,
                "description": entry.description,
                "symptoms": symptoms_text,
                "severity": entry.severity,
                "workflow_state": entry.workflow_state,
                "environment": entry.environment or "",
                "root_cause": entry.root_cause or "",
                "created_by": entry.created_by,
                "created_at": entry.created_at.isoformat(),
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.meilisearch_url}/indexes/entries/documents",
                    json=[document],
                    headers={"Authorization": f"Bearer {self.meilisearch_key}"},
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.info(f"Indexed entry {entry.id} in Meilisearch")

        except Exception as e:
            logger.error(f"Failed to index entry {entry.id} in Meilisearch: {e}")

    async def _generate_entry_embedding(self, entry: Entry):
        """Generate and store entry embedding."""
        try:
            # Combine text for embedding
            symptoms_text = " ".join([s.description for s in entry.symptoms])
            combined_text = f"{entry.title}\n\n{entry.description}\n\nSymptoms:\n{symptoms_text}"

            # Generate embedding
            response = await self.openai_client.embeddings.create(
                model=settings.embedding_model,
                input=combined_text,
            )

            embedding_vector = response.data[0].embedding

            # Store in database
            entry_embedding = EntryEmbedding(
                entry_id=entry.id,
                model_name=settings.embedding_model,
                dimension=len(embedding_vector),
                embedding=embedding_vector,
            )
            self.db.add(entry_embedding)
            await self.db.flush()

            logger.info(f"Generated embedding for entry {entry.id}")

        except Exception as e:
            logger.error(f"Failed to generate embedding for entry {entry.id}: {e}")

    async def _generate_solution_embedding(self, solution: Solution):
        """Generate and store solution embedding."""
        try:
            # Combine solution text
            steps_text = "\n".join([
                f"{s.order_index + 1}. {s.description}"
                for s in sorted(solution.steps, key=lambda x: x.order_index)
            ])
            combined_text = f"{solution.description}\n\nSteps:\n{steps_text}"

            # Generate embedding
            response = await self.openai_client.embeddings.create(
                model=settings.embedding_model,
                input=combined_text,
            )

            embedding_vector = response.data[0].embedding

            # Store in database
            solution_embedding = SolutionEmbedding(
                solution_id=solution.id,
                model_name=settings.embedding_model,
                dimension=len(embedding_vector),
                embedding=embedding_vector,
            )
            self.db.add(solution_embedding)
            await self.db.flush()

            logger.info(f"Generated embedding for solution {solution.id}")

        except Exception as e:
            logger.error(f"Failed to generate embedding for solution {solution.id}: {e}")

    async def delete_entry_from_index(self, entry_id: UUID):
        """Remove entry from Meilisearch."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.meilisearch_url}/indexes/entries/documents/{entry_id}",
                    headers={"Authorization": f"Bearer {self.meilisearch_key}"},
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.info(f"Deleted entry {entry_id} from Meilisearch")

        except Exception as e:
            logger.error(f"Failed to delete entry {entry_id} from Meilisearch: {e}")
