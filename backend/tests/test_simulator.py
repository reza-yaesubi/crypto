from app import config
from app.market import Simulator
from app.prices import PriceCache


def test_simulator_seeds_all_pairs():
    cache = PriceCache()
    Simulator(cache)
    pairs = {t.pair for t in cache.snapshot()}
    assert pairs == set(config.SEED_PRICES)


def test_step_moves_prices_and_keeps_them_positive():
    cache = PriceCache()
    sim = Simulator(cache, prices={"BTC-USD": 100.0}, vol=0.01)

    for _ in range(20):
        sim.step()

    tick = cache.get("BTC-USD")
    assert tick is not None
    assert tick.price > 0
    assert tick.price != 100.0  # movement occurred
    assert tick.direction in {"up", "down", "unchanged"}
