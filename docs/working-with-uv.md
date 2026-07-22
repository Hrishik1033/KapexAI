# Adding a dependency
# Add to a specific package
uv add --package backend "httpx>=0.27.0"

# Add to root (if you have root deps)
uv add "ruff" --dev

# Add to worker
uv add --package worker "redis>=5.0"
This updates both pyproject.toml and uv.lock in one command. Commit both files.
Team members sync
uv sync
That's it. uv.lock pins everything exactly, so everyone gets identical versions. Works the same as npm ci / pip install -r requirements.txt but faster.
Key tips
- Commit uv.lock -- this is what guarantees reproducible installs across the team
- Use --package flag when adding deps to backend/worker/db-service so it goes to the right pyproject.toml
- Dev deps use --dev flag (e.g. ruff, pytest, mypy) so they don't leak into production
- Run scripts with uv run instead of activating .venv -- e.g. uv run pytest, uv run --package backend uvicorn .... It auto-finds the right environment
- If someone pulls and uv sync fails, usually means uv.lock is stale -- run uv lock to regenerate
- Use uv tool for CLI tools you want globally (like ruff, prisma) instead of adding them as project deps: uv tool install ruff
- .venv is local -- never commit it. .gitignore it, each person runs uv sync to create their own