"""Server-Sent Events endpoint streaming live price updates."""

import json

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.prices import PriceCache

router = APIRouter()


@router.get("/api/stream/prices")
async def stream_prices(request: Request) -> EventSourceResponse:
    cache: PriceCache = request.app.state.price_cache
    queue = cache.subscribe()

    async def events():
        try:
            # Prime the client with the current snapshot, then stream updates.
            for tick in cache.snapshot():
                yield {"data": json.dumps(tick.to_dict())}
            while not await request.is_disconnected():
                tick = await queue.get()
                yield {"data": json.dumps(tick.to_dict())}
        finally:
            cache.unsubscribe(queue)

    return EventSourceResponse(events())
