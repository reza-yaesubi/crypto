"""Application configuration, sourced from environment variables."""

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

# SQLite database file. Defaults to <repo>/db/crypto.db; the container mounts
# /app/db as a volume and sets CRYPTO_DB_PATH accordingly.
DB_PATH = Path(os.environ.get("CRYPTO_DB_PATH", str(_REPO_ROOT / "db" / "crypto.db")))

STARTING_CASH = float(os.environ.get("CRYPTO_STARTING_CASH", "10000"))

DEFAULT_USER_ID = "default"

SEED_WATCHLIST = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "XRP-USD",
    "ADA-USD",
    "DOGE-USD",
    "AVAX-USD",
    "LINK-USD",
    "DOT-USD",
    "MATIC-USD",
]

# Market data
MARKET_DATA_SOURCE = os.environ.get("CRYPTO_MARKET_DATA_SOURCE", "simulator")
TICK_INTERVAL = float(os.environ.get("CRYPTO_TICK_INTERVAL", "0.5"))  # seconds
PER_TICK_VOL = float(os.environ.get("CRYPTO_PER_TICK_VOL", "0.0015"))  # ~0.15% std/tick

# Realistic seed prices for the simulator (USD).
SEED_PRICES = {
    "BTC-USD": 60000.0,
    "ETH-USD": 3000.0,
    "SOL-USD": 150.0,
    "XRP-USD": 0.50,
    "ADA-USD": 0.45,
    "DOGE-USD": 0.12,
    "AVAX-USD": 35.0,
    "LINK-USD": 15.0,
    "DOT-USD": 6.0,
    "MATIC-USD": 0.70,
}
