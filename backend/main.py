from contextlib import asynccontextmanager

from fastapi import FastAPI

from db_service import connect_db, disconnect_db, db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(title="KapexAI Backend", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
