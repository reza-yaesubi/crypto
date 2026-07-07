# Crypto — Cryptocurrency Trading Workstation

## Project Specification

> This plan adapts the proven `DETAILED_PLAN.md` architecture (borrowed from the
> "FinAlly" stock-trading capstone) to **cryptocurrency**, and correlates it with
> the tool/feed research in `RESEARCH.md`. The FinAlly simulated-portfolio model
> maps directly onto the research's safe Phase 1–2 (read-only → paper trading):
> the **free MVP is a paper-trading crypto workstation**, and real order execution
> is a later, gated phase. Cost options for scaling up are in Section 14.

## 1. Vision

Crypto is a visually stunning, AI-powered cryptocurrency trading workstation that
streams live market data, lets users trade a **simulated** portfolio, and
integrates an LLM chat assistant that can analyze positions and execute (paper)
trades on the user's behalf. It looks and feels like a modern Bloomberg terminal
with an AI copilot.

### Decisions locked in (2026-07-06)
- **Venue:** **Coinbase** (Advanced Trade) first — chosen for its documented
  sandbox, which lets us rehearse the live order flow with fake funds before Phase
  3. Execution is built on CCXT, so switching to Kraken later (lower fees) is a
  config change, not a rewrite.
- **Instruments:** Spot only for v1. No leverage, funding, perps, or DeFi.
- **Platform:** Web app (Next.js).
- **Money:** Simulated (paper) for the MVP. Real funds are a gated Phase 3.
- **Users:** MVP is single-user (`user_id = "default"`). Schema already carries
  `user_id` everywhere, so adding authentication and ~a dozen users later needs no
  migration. SQLite is fine at that scale; Postgres only if concurrency grows.
- **LLM:** Claude Opus 4.8 (`claude-opus-4-8`) is the default model, via LiteLLM
  (swappable to Haiku/Sonnet for cost). `LLM_MOCK=true` keeps tests/CI free.

## 2. User Experience

### First Launch
The user runs a single Docker command (or the start script). A browser opens to
`http://localhost:8000`. No login, no signup. They immediately see:
- A watchlist of 10 default crypto pairs with live-updating prices in a grid
- $10,000 in virtual USD cash
- A dark, data-rich trading terminal aesthetic
- An AI chat panel ready to assist

### What the User Can Do
- **Watch prices stream** — prices flash green (uptick) or red (downtick) with
  subtle CSS animations that fade
- **View sparkline mini-charts** — price action beside each ticker, accumulated on
  the frontend from the SSE stream since page load
- **Click a pair** to see a larger detailed chart in the main chart area
- **Buy and sell** — market orders only, instant fill at current price, no fees,
  no confirmation dialog (simulated money = zero stakes)
- **Monitor their portfolio** — a treemap heatmap of positions sized by weight and
  colored by P&L, plus a P&L chart of total portfolio value over time
- **View a positions table** — pair, quantity, average cost, current price,
  unrealized P&L, % change since average cost
- **Chat with the AI assistant** — ask about the portfolio, get analysis, and have
  the AI execute (paper) trades and manage the watchlist via natural language
- **Manage the watchlist** — add/remove pairs manually or via the AI chat

### Visual Design
- **Dark theme**: backgrounds around `#0d1117` / `#1a1a2e`, muted gray borders
- **Price flash animations**: brief green/red highlight on change, fading ~500ms
- **Connection status indicator**: colored dot (green connected / yellow
  reconnecting / red disconnected) in the header
- **Professional, data-dense layout** inspired by trading terminals
- **Responsive but desktop-first**: optimized for wide screens, functional on tablet
- Light/dark theming built in from day one

## 3. Architecture Overview

### Single Container, Single Port
```
┌─────────────────────────────────────────────────┐
│  Docker Container (port 8000)                    │
│                                                  │
│  FastAPI (Python/uv)                             │
│  ├── /api/*          REST endpoints              │
│  ├── /api/stream/*   SSE streaming               │
│  └── /*              Static file serving          │
│                      (Next.js export)             │
│                                                  │
│  SQLite database (volume-mounted)                │
│  Background task: market data polling/sim         │
└─────────────────────────────────────────────────┘
```

- **Frontend**: Next.js + TypeScript, static export (`output: 'export'`), served by
  FastAPI as static files
- **Backend**: FastAPI (Python), managed as a `uv` project
- **Database**: SQLite, single file at `db/crypto.db`, volume-mounted
- **Real-time data**: Server-Sent Events (SSE) — one-way server→client push
- **AI integration**: LiteLLM (model-agnostic), structured outputs for trades
- **Market data**: env-var driven — simulator by default; real data via a chosen
  provider adapter (CoinGecko / exchange native WS) if configured

### Why These Choices
| Decision | Rationale |
|---|---|
| SSE over WebSockets (frontend) | One-way push is all the UI needs; universal browser support. Backend may still consume an exchange WebSocket and re-push via SSE. |
| Static Next.js export | Single origin, no CORS, one port, one container |
| SQLite over Postgres | No auth = single-user = no DB server needed (MVP). Postgres is a Phase-3 option. |
| Single Docker container | One command to run; no orchestration |
| uv for Python | Fast, modern, reproducible lockfile (`uv run`, `uv add`) |
| Market orders only | No order book / limit / partial-fill logic — simpler portfolio math |
| CCXT for real execution | One code path across Coinbase/Kraken/others when Phase 3 arrives |
| LiteLLM for the LLM | Model swappable — free model for MVP, Claude for production |

## 4. Directory Structure
```
crypto/
├── frontend/                 # Next.js TypeScript project (static export)
├── backend/                  # FastAPI uv project (Python)
│   └── db/                   # Schema definitions, seed data, init logic
├── planning/                 # Project documentation (this file, RESEARCH.md, ...)
├── scripts/                  # start/stop scripts (Linux/macOS/Windows)
├── db/                       # Volume mount target (crypto.db lives here at runtime)
├── test/                     # Playwright E2E tests + docker-compose.test.yml
├── Dockerfile                # Multi-stage build (Node → Python)
├── docker-compose.yml        # Optional convenience wrapper
├── .env                      # Env vars (gitignored, .env.example committed)
└── .gitignore
```

## 5. Environment Variables

| Variable | Purpose | MVP default |
|---|---|---|
| `MARKET_DATA_SOURCE` | `simulator` \| `coingecko` \| `exchange_ws` | `simulator` |
| `COINGECKO_API_KEY` | CoinGecko API key (real data) | unset |
| `EXCHANGE` | `coinbase` \| `kraken` (native WS / CCXT) | `coinbase` |
| `LLM_PROVIDER` | LiteLLM model string | `claude-opus-4-8` |
| `ANTHROPIC_API_KEY` | key for Claude models | required (unless `LLM_MOCK`) |
| `LLM_MOCK` | `true` returns a deterministic mock (tests/CI) | `false` |
| `TRADING_MODE` | `paper` \| `live` (Phase 3 only) | `paper` |

Infra runs at **$0** with the MVP defaults (simulator/exchange-WS + SQLite +
local Docker). The only usage cost is the Claude Opus assistant (~cents/turn);
`LLM_MOCK=true` makes tests and CI free.

## 6. Market Data

### Two implementations, one interface
Both the simulator and each real provider implement the same abstract interface.
The backend selects one via `MARKET_DATA_SOURCE`. All downstream code (SSE, price
cache, frontend) is agnostic to the source.

### Simulator (default, free)
- Geometric Brownian motion (GBM) with per-pair drift/volatility
- Updates ~500ms; correlated moves across majors; occasional 2–5% "event" spikes
- Realistic crypto seed prices (e.g. BTC ~$60k, ETH ~$3k, SOL ~$150)
- In-process background task, no external dependencies

### Real providers (optional)
- **CoinGecko** (free tier): REST polling of the union of watched pairs. Free tier
  is rate-limited, so poll every ~15–30s (sparser sparklines are acceptable).
  Official MCP server available for the assistant later.
- **Exchange native WebSocket** (Coinbase/Kraken): free, low-latency ticker feed
  for the pairs actually traded; backend consumes the WS and re-pushes via SSE.

### Shared price cache
- A single background task (simulator or poller/WS) writes an in-memory cache of
  latest price, previous price, timestamp per pair
- SSE reads from the cache and pushes to clients
- "Known pairs" = union of watchlist + held positions

### SSE streaming
- Endpoint: `GET /api/stream/prices`; client uses native `EventSource`
- Server pushes ~500ms for all watched/held pairs
- Event JSON:
  ```json
  {"pair": "BTC-USD", "price": 61250.5, "prev_price": 61180.2,
   "timestamp": "2026-07-06T10:00:00Z", "direction": "up"}
  ```
  `direction`: `up` | `down` | `unchanged`
- Frontend flashes only when `price !== prev_price`
- EventSource auto-reconnects

## 7. Database (SQLite, lazy init)
Backend creates the schema and seeds defaults on first request if the DB is empty.
All tables carry a `user_id` defaulting to `"default"` (single-user now,
multi-user later without migration).

- **users_profile** — `id` PK (`"default"`), `cash_balance` REAL (default `10000.0`), `created_at`
- **watchlist** — `id` PK (UUID), `user_id`, `pair`, `added_at`; UNIQUE `(user_id, pair)`
- **positions** — `id` PK, `user_id`, `pair`, `quantity` REAL (fractional), `avg_cost` REAL, `updated_at`; UNIQUE `(user_id, pair)`
- **trades** — `id` PK, `user_id`, `pair`, `side` (`buy`/`sell`), `quantity`, `price`, `executed_at`
- **portfolio_snapshots** — `id` PK, `user_id`, `total_value` REAL, `recorded_at` (every 30s + after each trade)
- **chat_messages** — `id` PK, `user_id`, `role` (`user`/`assistant`), `content`, `actions` (JSON), `created_at`

### Default seed data
- One user: `id="default"`, `cash_balance=10000.0`
- Ten watchlist pairs: BTC-USD, ETH-USD, SOL-USD, XRP-USD, ADA-USD, DOGE-USD,
  AVAX-USD, LINK-USD, DOT-USD, MATIC-USD

## 8. API Endpoints

### Market Data
| Method | Path | Description |
|---|---|---|
| GET | `/api/stream/prices` | SSE stream of live price updates |

### Portfolio
| Method | Path | Description |
|---|---|---|
| GET | `/api/portfolio` | Positions, cash, total value, unrealized P&L |
| POST | `/api/portfolio/trade` | Execute a (paper) trade: `{pair, quantity, side}` |
| GET | `/api/portfolio/history` | Value snapshots over time (P&L chart) |

`GET /api/portfolio` returns `{cash, total_value, positions:[{pair, quantity, avg_cost, current_price, unrealized_pnl, pnl_pct}]}`.
Trade validation: buys need `quantity*price <= cash`; sells need `quantity <= position.quantity`; `quantity > 0`.

### Watchlist
| Method | Path | Description |
|---|---|---|
| GET | `/api/watchlist` | Current pairs (prices come from SSE) |
| POST | `/api/watchlist` | Add a pair `{pair}` |
| DELETE | `/api/watchlist/{pair}` | Remove a pair |

### Chat
| Method | Path | Description |
|---|---|---|
| POST | `/api/chat` | Send a message; receive message + executed actions |

Request `{"message": "Buy 0.1 BTC"}` → response `{"message": "...", "trades": [...], "watchlist_changes": [...]}`.

### System
| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |

## 9. LLM Integration

### Claude Opus 4.8 via LiteLLM
All LLM calls go through **LiteLLM** with **structured outputs**, so the model is a
config value (`LLM_PROVIDER`), not hardcoded.

- **Default model:** **Claude Opus 4.8** (`claude-opus-4-8`) via the Anthropic
  provider — strongest analysis and tool-calling. ~$0.02–0.04 per chat turn.
- **Cost fallbacks (swap `LLM_PROVIDER`, no code change):** Claude Sonnet 5
  (`claude-sonnet-5`) or Claude Haiku 4.5 (`claude-haiku-4-5`) for high volume.
- When building the integration, consult the `claude-api` skill. The Claude Agent
  SDK is a first-class MCP client for later wiring the CoinGecko/CCXT MCP servers.

### How it works
On a chat message the backend:
1. Loads portfolio context (cash, positions with P&L, watchlist with live prices, total value)
2. Loads the last 20 `chat_messages` as history
3. Builds a prompt (system + context + history + new message)
4. Calls the LLM via LiteLLM requesting structured output
5. Parses the structured JSON
6. Auto-executes trades / watchlist changes (**paper mode only** — see below)
7. Stores the message + actions
8. Returns the complete JSON (no token streaming; a loading indicator suffices)

### Structured output schema
```json
{
  "message": "conversational response",
  "trades": [{"pair": "BTC-USD", "side": "buy", "quantity": 0.1}],
  "watchlist_changes": [{"pair": "SOL-USD", "action": "add"}]
}
```
Each trade passes the same validation as manual trades. `watchlist_changes.action`
is `add` only.

### Auto-execution and the safety boundary
- **Paper mode (MVP):** trades the LLM proposes execute automatically, no
  confirmation — fake money, zero stakes, fluid demo, showcases agentic AI.
- **Live mode (Phase 3):** auto-execution is **disabled**. Every LLM-proposed order
  requires explicit human confirmation, keys are scoped trade-only (no withdrawal),
  and per-order notional caps apply. This is the one hard rule carried over from
  `RESEARCH.md`.

### System prompt
Prompt the assistant as "Crypto, an AI trading assistant" — analyze composition /
concentration / P&L, suggest trades with reasoning, execute when asked, manage the
watchlist, be concise and data-driven, always return valid structured JSON.

### LLM mock mode
`LLM_MOCK=true` returns a deterministic response for fast, free, reproducible E2E
tests and CI — no API key needed.

## 10. Frontend Design
Single-page, dense, terminal-inspired layout including:
- **Watchlist panel** — pair, current price (flashing), % change since first seen,
  sparkline (from SSE)
- **Main chart area** — larger chart for the selected pair (TradingView
  **Lightweight Charts** — 45KB, built for streaming OHLCV)
- **Portfolio heatmap** — treemap sized by weight, colored by P&L
- **P&L chart** — total value over time (from `portfolio_snapshots`)
- **Positions table** — pair, quantity, avg cost, current price, unrealized P&L, %
- **Trade bar** — pair + quantity fields, buy/sell buttons, market orders
- **AI chat panel** — docked/collapsible; input, history, loading indicator; trade
  / watchlist actions shown inline
- **Header** — total value (live), connection status dot, cash balance

Technical notes: `EventSource` for SSE; Lightweight Charts for price, ECharts/
Recharts for auxiliary panels; CSS flash on price change; same-origin `/api/*` (no
CORS); Tailwind with a custom dark theme.

## 11. Docker & Deployment
Multi-stage Dockerfile: Stage 1 (Node) builds the Next.js static export; Stage 2
(Python + uv) `uv sync`, copies the frontend build into `static/`, exposes 8000,
runs uvicorn. SQLite persists via a named volume
(`docker run -v crypto-data:/app/db -p 8000:8000 --env-file .env crypto`).
Idempotent start/stop scripts for Linux/macOS/Windows. Optional cloud deploy
(Render / AWS App Runner) is a stretch goal.

## 12. Testing Strategy
- **Backend (pytest):** simulator GBM correctness, real-provider response parsing,
  interface conformance; trade execution + P&L edge cases; LLM structured-output
  parsing + malformed handling + trade validation in chat; API status codes /
  shapes / errors.
- **Frontend (React Testing Library):** component rendering, price-flash trigger,
  watchlist CRUD, portfolio calculations, chat rendering + loading.
- **E2E (Playwright, `test/`):** `docker-compose.test.yml` app + Playwright
  containers; run with `LLM_MOCK=true`. Scenarios: fresh start (default watchlist,
  $10k, streaming prices), add/remove pair, buy (cash down, position appears), sell,
  heatmap + P&L render, AI chat (mocked) with inline trade, SSE reconnect.

## 13. Phased Roadmap
```
Phase 1  MVP — read-only + paper workstation   [infra $0, LLM ~cents/turn]
  Next.js + Lightweight Charts  <-- SSE  simulator (or exchange WS / CoinGecko free)
  FastAPI + SQLite, single-user, simulated $10k portfolio, market orders
  LiteLLM assistant on Claude Opus 4.8, paper auto-execution
  Local TA (pandas-ta) optional; Fear & Greed tile optional

Phase 2  Richer data + analysis                     [low cost]
  Real-time via exchange WS (free); LunarCrush sentiment tile
  Backtesting (backtrader/vectorbt); optional auth + multi-user

Phase 3  Live trading (gated, opt-in)               [real money]
  CCXT against Coinbase/Kraken testnet -> real, trade-only keys
  Human confirmation on every order + notional caps; Postgres for history
  On-chain intel (Glassnode/Nansen) as budget allows
```

## 14. Cost Model

### MVP — infra $0, LLM ~cents/turn
| Component | Choice | Cost |
|---|---|---|
| Market data | Simulator, or exchange native WS, or CoinGecko free tier | $0 |
| LLM | Claude Opus 4.8 via LiteLLM (or `LLM_MOCK` for tests) | ~$0.02–0.04/turn ($0 mocked) |
| Charting | TradingView Lightweight Charts (open source) | $0 |
| Backend/DB | FastAPI + SQLite (single-user) | $0 |
| Execution | Simulated (paper) | $0 |
| Hosting | Local Docker | $0 |

### Real-time market data is free — no paid tier needed
For spot pairs on Coinbase/Kraken, the **exchange's own native WebSocket** streams
real-time ticker/trade data at **$0** (no API key for public data), covering
exactly the pairs traded. This is the recommended real-time source; CoinGecko is
only a supplement.

| Real-time source | Real-time? | Cost | Notes |
|---|---|---|---|
| Coinbase / Kraken native WS | Yes, sub-second | **$0** | Traded pairs; recommended |
| CoinGecko Demo (free) | No (REST poll ~15–30s) | $0 | Broad aggregate prices + metadata |
| CoinGecko Basic | No (REST, 300/min) | ~$35/mo | Faster polling, still no WS |
| CoinGecko Analyst | Yes (aggregated WS) | ~$129/mo | Only for cross-exchange aggregation |

### Other next-phase paid options (choose as needed)
| Upgrade | Provider | Approx. cost | When |
|---|---|---|---|
| Institutional / cross-exchange data | Kaiko | Enterprise | only if needed |
| Production LLM | Claude Opus 4.8 (`claude-opus-4-8`) | $5 / $25 per 1M input/output tokens (~$0.02–0.04 per chat turn) | Phase 2–3 |
| Cheaper production LLM | Claude Haiku 4.5 (`claude-haiku-4-5`) | $1 / $5 per 1M (~$0.005–0.01 per turn) | high volume |
| Balanced LLM | Claude Sonnet 5 (`claude-sonnet-5`) | $3 / $15 per 1M | middle option |
| Sentiment | LunarCrush | paid tiers | Phase 2 |
| On-chain intel | Glassnode / Nansen | paid tiers | Phase 3 |
| Real execution | CCXT (free lib) + exchange | exchange spot fees ~0.1–0.6% per trade | Phase 3 |
| Hosting | Render / AWS App Runner | ~$0–25/mo small instance | when shared |

Per-chat-turn LLM estimates assume ~2–4K input tokens (portfolio context + history)
and ~500 output tokens; verify against live pricing before committing.

## 15. Resolved & remaining

Resolved (2026-07-06): venue = **Coinbase** (swappable via CCXT); **single-user**
MVP with `user_id` schema ready for ~a dozen users + auth later; LLM = **Claude
Opus 4.8**.

Remaining before Phase 3 (live trading):
1. Confirm the regulatory posture for executing real trades on behalf of ~a dozen
   users (vs. personal use) — may carry licensing implications.
2. Design the authentication + per-user isolation approach (deferred to Phase 2/3).

See `RESEARCH.md` for the full tool/feed/MCP survey behind these choices.
