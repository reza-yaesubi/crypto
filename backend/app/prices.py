"""In-memory price cache with a simple asyncio pub/sub for SSE fan-out."""

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class PriceTick:
    pair: str
    price: float
    prev_price: float
    timestamp: str
    direction: str  # "up" | "down" | "unchanged"

    def to_dict(self) -> dict:
        return asdict(self)


class PriceCache:
    """Holds the latest tick per pair and broadcasts updates to subscribers."""

    def __init__(self) -> None:
        self._ticks: dict[str, PriceTick] = {}
        self._subscribers: set[asyncio.Queue] = set()

    def update(self, pair: str, price: float) -> PriceTick:
        prev = self._ticks.get(pair)
        prev_price = prev.price if prev else price
        if price > prev_price:
            direction = "up"
        elif price < prev_price:
            direction = "down"
        else:
            direction = "unchanged"

        tick = PriceTick(
            pair=pair,
            price=price,
            prev_price=prev_price,
            timestamp=datetime.now(timezone.utc).isoformat(),
            direction=direction,
        )
        self._ticks[pair] = tick

        for queue in list(self._subscribers):
            try:
                queue.put_nowait(tick)
            except asyncio.QueueFull:
                pass  # slow consumer: drop this tick, next one will follow
        return tick

    def get(self, pair: str) -> PriceTick | None:
        return self._ticks.get(pair)

    def snapshot(self) -> list[PriceTick]:
        return list(self._ticks.values())

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)
