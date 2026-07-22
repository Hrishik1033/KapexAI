# KapexAI — Agent Guide

## Workspace

uv workspace monorepo (Python >=3.12). Packages: `backend/`, `worker/`, `services/database/` (published as `db-service`). `frontend/` is a placeholder (empty).

## Essential commands

| Command | What it does |
|---|---|
| `make install` | `uv sync` — install all workspace packages |
| `make generate` | `uv run prisma generate --schema=services/database/schema.prisma` — regenerate Prisma client after schema changes |
| `make migrate` | `uv run prisma migrate dev --schema=services/database/schema.prisma` — create & apply a new migration |
| `make dev-backend` | `uv run --package backend uvicorn backend.main:app --reload` — start FastAPI dev server |
| `make dev-worker` | `uv run --package worker python -m worker.main` — start worker |

## Dependency management

Use `uv add --package <pkg> <dep>` (never `pip install`). Example:
- `uv add --package backend "httpx>=0.27.0"`
- `uv add --package worker "redis>=5.0"`
- `uv add --dev "ruff"` (root dev dep)

`uv run` replaces virtualenv activation — it auto-finds the right environment.

## Database

- ORM: Prisma, schema at `services/database/schema.prisma`
- Provider: PostgreSQL
- Connection string via `DATABASE_URL` env var (`.env`)
- Shared client: `from db_service import db, connect_db, disconnect_db`
- After editing `schema.prisma`, run `make generate` then `make migrate`
- `.prisma/` is gitignored (generated Prisma client)

## OpenCode

Custom commands in `.opencode/commands/`:
- `start-work` — syncs main with upstream and creates a feature branch
- `pr-prep` — analyzes changes, generates tests, drafts PR description

## State of project

Early stage — backend and worker have boilerplate main modules using `db_service`. No test runner or linter configured.

## Boilerplate code

| File | Description |
|---|---|
| `backend/main.py` | FastAPI app with `/health` endpoint; connects DB on startup |
| `worker/main.py` | Async event loop worker; connects DB and handles graceful shutdown |

Before running either, ensure the Prisma client is generated: `make generate`.
