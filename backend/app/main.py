"""FastAPI application entry point."""

import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import database, market, stream
from app.prices import PriceCache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Init the database and run the market-data source for the app's lifetime."""
    database.init_db()

    cache = PriceCache()
    app.state.price_cache = cache
    source = market.get_source(cache)
    stop = asyncio.Event()
    task = asyncio.create_task(source.run(stop))
    try:
        yield
    finally:
        stop.set()
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


def create_app() -> FastAPI:
    app = FastAPI(title="Crypto Trading Workstation", lifespan=lifespan)
    app.include_router(stream.router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
