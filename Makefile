.PHONY: install generate migrate dev

install:
	uv sync

generate:
	uv run prisma generate --schema=services/database/schema.prisma

migrate:
	uv run prisma migrate dev --schema=services/database/schema.prisma

dev-backend:
	uv run --package backend uvicorn backend.main:app --reload

dev-worker:
	uv run --package worker python -m worker.main