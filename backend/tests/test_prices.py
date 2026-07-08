import asyncio

from app.prices import PriceCache


def test_update_computes_direction():
    cache = PriceCache()

    first = cache.update("BTC-USD", 100.0)
    assert first.direction == "unchanged"  # no prior price

    up = cache.update("BTC-USD", 110.0)
    assert up.direction == "up"
    assert up.prev_price == 100.0

    down = cache.update("BTC-USD", 105.0)
    assert down.direction == "down"
    assert down.prev_price == 110.0


def test_snapshot_holds_latest_per_pair():
    cache = PriceCache()
    cache.update("BTC-USD", 100.0)
    cache.update("ETH-USD", 50.0)
    cache.update("BTC-USD", 101.0)

    latest = {t.pair: t.price for t in cache.snapshot()}
    assert latest == {"BTC-USD": 101.0, "ETH-USD": 50.0}


def test_subscriber_receives_updates():
    async def scenario():
        cache = PriceCache()
        queue = cache.subscribe()
        cache.update("BTC-USD", 100.0)
        tick = await asyncio.wait_for(queue.get(), timeout=1)
        assert tick.pair == "BTC-USD"
        assert tick.price == 100.0

        cache.unsubscribe(queue)
        cache.update("BTC-USD", 101.0)
        assert queue.empty()  # no longer subscribed

    asyncio.run(scenario())
