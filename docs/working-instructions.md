# KapexAI — Working Instructions

Welcome to the team! This guide covers everything you need to get up and running.

---

## Prerequisites

- **Python 3.12+** — check with `python --version`
- **[uv](https://docs.astral.sh/uv/)** — the package manager for this project. Install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify: `uv --version`

---

## Project structure

This is a **uv workspace monorepo** — a single repo with multiple Python packages that share a lockfile:

```
kapex-ai/
├── backend/                  # FastAPI web server (package: backend)
│   └── pyproject.toml
├── worker/                   # Background worker (package: worker)
│   └── pyproject.toml
├── services/database/        # Shared Prisma DB client (package: db-service)
│   ├── db_service/
│   ├── schema.prisma
│   └── pyproject.toml
├── pyproject.toml            # Root workspace config
├── uv.lock                   # Single lockfile for all packages
└── Makefile
```

Packages reference each other via `[tool.uv.sources]` with `workspace = true`, so `db-service` is automatically available to `backend` and `worker` without publishing to PyPI.

---

## First-time setup

### 1. Clone and install

```bash
git clone <repo-url>
cd kapex-ai
uv sync
```

`uv sync` reads `uv.lock` and installs **all** workspace packages (backend, worker, db-service) with their exact versions. This is the only command you need — no `pip install`, no virtualenv activation.

### 2. Set up the `.env` file

The database connection string comes from a `.env` file at the project root:

```bash
cp .env.example .env    # if there's an example file
```

Or create `.env` with:

```
DATABASE_URL="postgresql://user:password@host:5432/mydb?sslmode=require"
```

The `.env` file is in `.gitignore` — **it will never be committed**. Each dev creates their own.

> **Where does this URL come from?** Ask the lead dev for the database credentials. In production it comes from a vault / CI secret.

### 3. Generate the Prisma client

Prisma needs to generate its Python client from the schema:

```bash
make generate
```

This runs `uv run prisma generate --schema=services/database/schema.prisma`. The output goes to `.prisma/` (gitignored). You need to do this once after cloning, and again whenever the schema changes.

### 4. Run database migrations (only in case you have changed the schema.. otherwise ignore this command)

```bash
make migrate
```

This applies any pending migrations to your local database. If you're setting up from scratch, this creates all tables.

---

## Daily commands (Makefile)

| Command | What it does |
|---|---|
| `make install` | `uv sync` — install/update all dependencies |
| `make generate` | Regenerate Prisma client after schema changes |
| `make migrate` | Create & apply a new Prisma migration |
| `make dev-backend` | Start the FastAPI dev server at `http://localhost:8000` |
| `make dev-worker` | Start the background worker |

---

## Running the app

**Backend** (FastAPI):

```bash
make dev-backend
```

Open http://localhost:8000/docs for the interactive Swagger UI.
The `/health` endpoint should return `{"status": "ok"}`.

**Worker**:

```bash
make dev-worker
```

Hit Ctrl+C to stop either one.

---

## Adding dependencies

This is the part beginners trip up on. **Never use `pip install`** — it bypasses the lockfile and breaks other devs' environments.

### Add a dependency to a specific package

```bash
uv add --package backend "httpx>=0.27.0"
uv add --package worker "redis>=5.0"
uv add --package db-service "pydantic>=2.0"
```

### Add a dev-only dependency (root level)

```bash
uv add --dev "ruff"
uv add --dev "pytest>=8.0"
```

### What this does

- Updates the correct `pyproject.toml` (e.g., `backend/pyproject.toml`)
- Updates `uv.lock` with the resolved version

### After adding a dependency, you must commit TWO things

```
git add backend/pyproject.toml uv.lock
git commit -m "add httpx dependency"
```

If you only commit `pyproject.toml`, other devs will get an error when running `uv sync` because the lockfile is out of date. If you only commit `uv.lock`, their `pyproject.toml` won't list the dep. **Always commit both.**

### What other devs do when they pull your change

```bash
git pull
uv sync
```

That's it. `uv.lock` pins the exact versions so everyone gets the same thing — no more "works on my machine".

---

## Database & Prisma

### Schema

The schema is at `services/database/schema.prisma`.

### After editing the schema

```bash
make generate    # regenerate the Python client
make migrate     # create + apply a migration
```

Commit the generated migration files (they live in `services/database/migrations/`):

```bash
git add services/database/ uv.lock pyproject.toml
git commit -m "add foobar model to schema"
```

### Using the DB client in code

```python
from db_service import db, connect_db, disconnect_db

await connect_db()
users = await db.user.find_many()  # fully typed
await disconnect_db()
```

The `db_service` package is a shared library inside the monorepo — it's not published to PyPI. Changes to `services/database/` are instantly available to `backend` and `worker` without any install step.

---

## Troubleshooting

| Problem | Likely fix |
|---|---|
| `uv sync` fails with checksum error | Run `uv lock` to regenerate `uv.lock`, then `uv sync` |
| `ModuleNotFoundError: prisma` | Run `make generate` — the Prisma client hasn't been generated |
| `DATABASE_URL` not found | Create a `.env` file at the project root with the connection string |
| Migration conflicts | Run `make migrate` — if it fails, ask the team about conflicting migration history |
| Port 8000 already in use | Kill the other process or change the port: `uv run --package backend uvicorn backend.main:app --reload --port 8001` |
| Dependency version conflict | Use `uv tree` to see what's pulling incompatible versions |

---

## Key rules

1. **Never commit `.env`** — it's in `.gitignore` for a reason
2. **Never commit `.venv/`** — each dev runs `uv sync` to create their own
3. **Always commit `uv.lock` alongside `pyproject.toml`** — this is how dependency changes reach the team
4. **Run `make generate` after every schema change** — missing this causes confusing import errors
5. **Use `uv run` instead of activating `.venv`** — it auto-finds the right environment

---

## Cheatsheet

```bash
# install everything
uv sync

# add to backend
uv add --package backend "some-pkg>=1.0"

# add to worker
uv add --package worker "some-pkg>=1.0"

# add a dev tool (root level)
uv add --dev "ruff"

# run something
uv run --package backend python -c "print('hi')"

# see dependency tree
uv tree
```

If anything is unclear, ask other devs — we're all learning this together.
