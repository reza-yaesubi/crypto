"""Market-data sources. The simulator is the default; real providers plug in here.

All sources write to a shared PriceCache, so downstream code (SSE, price reads)
is agnostic to where prices come from.
"""

import asyncio
import math
import random

from app import config
from app.prices import PriceCache


class Simulator:
    """Generates correlated random-walk prices via per-tick lognormal steps."""

    def __init__(
        self,
        cache: PriceCache,
        prices: dict[str, float] | None = None,
        interval: float | None = None,
        vol: float | None = None,
    ) -> None:
        self.cache = cache
        self.interval = interval if interval is not None else config.TICK_INTERVAL
        self.vol = vol if vol is not None else config.PER_TICK_VOL
        self._prices = dict(prices if prices is not None else config.SEED_PRICES)
        for pair, price in self._prices.items():
            cache.update(pair, price)

    def step(self) -> None:
        """Advance every pair by one tick and publish to the cache."""
        market = random.gauss(0, 1)  # shared factor -> correlated moves
        for pair, price in self._prices.items():
            z = 0.5 * market + 0.5 * random.gauss(0, 1)
            price *= math.exp(-0.5 * self.vol**2 + self.vol * z)
            if random.random() < 0.002:  # occasional event spike
                price *= 1 + random.uniform(-0.05, 0.05)
            self._prices[pair] = price
            self.cache.update(pair, price)

    async def run(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            self.step()
            try:
                await asyncio.wait_for(stop.wait(), timeout=self.interval)
            except asyncio.TimeoutError:
                pass


def get_source(cache: PriceCache) -> Simulator:
    """Build the market-data source selected by config.MARKET_DATA_SOURCE."""
    if config.MARKET_DATA_SOURCE == "simulator":
        return Simulator(cache)
    raise ValueError(f"Unknown MARKET_DATA_SOURCE: {config.MARKET_DATA_SOURCE!r}")
