from contextlib import asynccontextmanager
from pydantic import BaseModel, EmailStr

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db_service import connect_db, disconnect_db, db


# Pydantic model for waitlist signup request
class WaitlistSignup(BaseModel):
    email: EmailStr
    name: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(title="KapexAI Backend", lifespan=lifespan)

# CORS middleware to allow requests from localhost:3000 (frontend dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/waitlist")
async def join_waitlist(signup: WaitlistSignup):
    """Add email (and optional name) to waitlist. Returns success message."""
    # In a real app, you'd save to database here, e.g.:
    # await db.waitlist.create(data={"email": signup.email, "name": signup.name})
    return {"message": "Successfully joined the waitlist!", "email": signup.email}