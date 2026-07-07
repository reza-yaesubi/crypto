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
