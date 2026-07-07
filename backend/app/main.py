"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database (create + seed if empty) on startup."""
    database.init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Crypto Trading Workstation", lifespan=lifespan)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
