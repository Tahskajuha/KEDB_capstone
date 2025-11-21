# KEDB Platform

Enterprise knowledge database with AI-powered incident resolution. Captures symptoms, solutions, and execution steps with full audit trails and workflow management.

## Architecture

**Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 + pgvector  
**Search:** Meilisearch (lexical) + pgvector (semantic)  
**Queue:** Redis + RQ for async workers  
**AI:** OpenAI/Anthropic integration with citation tracking

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                        │
│                    (Web UI / API Clients)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────┐
│                      FastAPI Backend                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  CRUD API    │  │  Search API  │  │  Agent API   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────-┬──────┘      │
│         │                 │                  │             │
│  ┌──────▼─────────────────▼──────────────────▼───────┐     │
│  │            Service Layer + Auth                   │     │
│  └──────┬─────────────────┬──────────────────┬───────┘     │
└─────────┼─────────────────┼──────────────────┼─────────────┘
          │                 │                  │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌──────▼──────┐
    │PostgreSQL │    │Meilisearch│    │   Redis     │
    │+ pgvector │    │  (BM25)   │    │   (Queue)   │
    └───────────┘    └───────────┘    └──────┬──────┘
                                             │
                                      ┌──────▼──────-─┐
                                      │  RQ Workers   │
                                      │(Async Tasks)  │
                                      └───────────────┘
```

### Data Flow: AI Agent Suggestions

```
User Query → Agent API
      │
      ├─→ Semantic Search (pgvector cosine similarity)
      │   └─→ Top-K entries by embedding distance
      │
      ├─→ Lexical Search (Meilisearch BM25)
      │   └─→ Keyword matches with filters
      │
      └─→ Hybrid Results
          │
          ├─→ Cross-encoder Re-ranking
          │   └─→ Score recalculation for precision
          │
          └─→ LLM Synthesis (OpenAI/Anthropic)
              ├─→ Citation extraction (entry_id/solution_id)
              ├─→ Policy check (RBAC enforcement)
              └─→ Response with evidence + scores
```

### Database Entity Relationships

```
Entry ──┬─→ EntrySymptom (1:N)
        ├─→ EntryIncident (1:N)
        ├─→ EntryEmbedding (1:N)
        ├─→ Solution (1:N)
        │   ├─→ SolutionStep (1:N)
        │   └─→ SolutionEmbedding (1:N)
        ├─→ EntryTag (M:N) ←─→ Tag
        ├─→ Review (1:N)
        │   └─→ ReviewParticipant (1:N)
        └─→ AuditLog (1:N)

AgentSession ──┬─→ AgentCall (1:N)
               ├─→ AgentSuggestion (1:N)
               └─→ PolicyDecision (1:N)
```

## Core Features

**Entry Management** (Implemented)
- Workflow states: Draft → InReview → Published → Retired/Merged
- Multi-solution support with ordered execution steps
- Symptom tracking and incident linking (PagerDuty, Opsgenie)
- Full CRUD API with pagination and filtering
- Automated test coverage with 100% pass rate

**AI Agent** (Planned - Phase D)
- `/agent/suggest` - Returns cited recommendations with evidence scores
- `/agent/run` - Guarded tool execution with RBAC policy enforcement
- Token usage and cost tracking per session

**Search** (Planned - Phase C)
- Dual retrieval: BM25 lexical + vector semantic search
- Cross-encoder re-ranking for precision
- 3072-dimension embeddings (text-embedding-3-large)

**Governance** (Partially Implemented)
- Multi-participant review workflow (API implemented, testing pending)
- Complete audit logs with JSON diffs (schema ready)
- Analytics: MTTR deltas, adoption metrics, content health (planned)

## Database Schema

21 tables across 8 model files:
- Core: entries, solutions, solution_steps, tags
- Embeddings: entry_embeddings, solution_embeddings
- Agent: agent_sessions, agent_calls, agent_suggestions, policy_decisions
- Workflow: reviews, review_participants
- Audit: audit_logs, suggestion_events
- Utilities: prompts, attachments, synonyms

## Setup

**Prerequisites**
- Python 3.13+ (3.14 not yet supported due to asyncpg)
- Poetry 2.2+
- Docker Desktop

**Quick Start (Automated)**

```bash
# Run the automated setup script
chmod +x setup_phase_a.sh
./setup_phase_a.sh
```

This script will:
1. Install Python dependencies via Poetry
2. Start Docker services (Postgres, Redis, Meilisearch)
3. Enable pgvector extension
4. Run database migrations
5. Verify installation

**Manual Installation**

```bash
# Start infrastructure
docker compose -f deploy/docker-compose.yml up -d

# Install dependencies
cd backend
poetry install

# Run migrations
poetry run alembic upgrade head

# Start API
poetry run uvicorn app.main:app --reload --port 8080
```

**Database Services**
- PostgreSQL: localhost:5432 (kedb/kedb/kedb)
- Redis: localhost:6379
- Meilisearch: localhost:7700

## Project Structure

```
backend/
  app/
    models/       # SQLAlchemy ORM models
    api/          # FastAPI endpoints
    agent/        # AI agent logic
    search/       # Search integrations
    services/     # Business logic
    workers/      # Background jobs
  alembic/        # Database migrations
  tests/          # Test suite

deploy/
  docker-compose.yml

plan/
  # Architecture diagrams and specs
```

## API Documentation

The CRUD API is fully operational with 30 endpoints for managing entries, solutions, tags, and reviews.

**Quick Start:**
- API Server: `http://localhost:8080`
- Interactive Docs: `http://localhost:8080/docs` (Swagger UI)
- OpenAPI Spec: `http://localhost:8080/api/v1/openapi.json`

**Endpoint Categories:**
- Entry Management: 8 endpoints (create, read, update, delete, list, symptoms, incidents)
- Solution Management: 9 endpoints (CRUD + step management)
- Tag Management: 8 endpoints (CRUD + entry tagging)
- Review Workflow: 5 endpoints (review creation, participants, decisions)

For complete endpoint documentation, request/response examples, and testing results, see [CRUD_Endpoints.md](./CRUD_Endpoints.md).

## Development Status

**Phase A (Bootstrap) - Complete**
- Database schema and migrations (21 tables)
- Docker infrastructure (PostgreSQL, Redis, Meilisearch)
- Health checks and testing framework
- Alembic migration system

**Phase B (CRUD API) - Complete**
- 30 REST endpoints across 4 resources (Entries, Solutions, Tags, Reviews)
- Repository pattern implementation (5 repositories)
- Service layer with business logic (5 services)
- Pydantic schemas with validation (25+ schemas)
- Complete test suite (7 automated tests, 100% pass rate)
- Error handling and transaction management

For detailed endpoint documentation, API testing results, and bug fixes, see [CRUD_Endpoints.md](./CRUD_Endpoints.md).

**Next Phases:**
- Phase C: Search integration (Meilisearch + pgvector semantic search)
- Phase D: AI agent implementation (OpenAI/Anthropic with citation tracking)
- Phase E: Workflow automation and review processes
- Phase F: Analytics dashboard and MTTR metrics
