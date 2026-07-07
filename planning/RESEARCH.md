# Research — Tools, Feeds, MCP Servers & AI for the Crypto Trading Workstation

Research date: 2026-07-06. This document surveys the building blocks for the app
described in `PLAN.md`: a visually stunning, AI-powered trading workstation that
streams live market data, provides analysis, and runs an LLM chat assistant that
can analyze positions and execute trades.

The app decomposes into seven layers. Each section below lists the credible
options as of mid-2026, then gives a recommendation. A consolidated MVP stack is
at the end.

---

## Summary — recommended MVP stack

| Layer | Pick for MVP | Why |
|---|---|---|
| Market data (REST + WS) | CoinGecko API + its MCP server | Broad coverage, transparent pricing, official MCP, sub-second WS |
| Execution / exchange | CCXT (Python) targeting one CEX first (Coinbase or Kraken) | Free, mature, 100+ exchanges, one code path |
| MCP bridge for the LLM | CoinGecko MCP (data) + CCXT MCP (execution) | Splits read-only data from trade actions cleanly |
| On-chain + sentiment | Defer to phase 2; start with CoinMarketCap Fear & Greed + LunarCrush | Cheap signals, no heavy infra to start |
| AI / LLM assistant | Claude (Opus 4.8) via Claude Agent SDK + tool-use | Native to this project; strong tool-calling; MCP client built in |
| Charting / frontend | TradingView Lightweight Charts + Next.js/React | Free, 45KB, purpose-built for streaming OHLCV |
| Trade safety | Paper-trading / testnet first, human confirm on every order | Non-negotiable before real funds |

Guiding principle from `CLAUDE.md`: build incrementally. Start read-only (data +
analysis + chat), add **paper** execution, and only then wire real orders behind
explicit confirmation.

---

## Layer 1 — Market data feeds (prices, OHLCV, order books)

Real-time streaming (WebSocket) plus historical REST is the core feed.

| Provider | Strengths | Notes / pricing |
|---|---|---|
| **CoinGecko API** | 18k+ CEX coins, 37M+ DEX tokens, 250+ networks, sub-second WS, 99.9% SLA, SOC-2, official MCP server | ~$129/mo for WS access; strong default |
| **CoinMarketCap API** | Ranked discovery, screeners, movers, Fear & Greed index; Pro API WS beta (June 2026) | Good for discovery UX; official MCP server |
| **Kaiko** | Institutional order-book depth + derivatives; SOC-2, 99.9% SLA | Enterprise budget |
| **CoinAPI / Coinbase / Kraken native WS** | Direct venue feeds, lowest latency for the venue you trade on | Free from the exchange you use |
| **CryptoFeed** (Python lib) | High-performance WS aggregation across many venues | Free, self-hosted; data-only, no execution |
| **Bitquery / DexPaprika** | On-chain / DEX liquidity, TVL, pools | DexPaprika free, no API key |

**Recommendation:** CoinGecko API for breadth + its MCP server for the assistant.
For the venue you actually trade on, also consume that exchange's native WebSocket
directly (lower latency, free) via CCXT Pro or CryptoFeed.

---

## Layer 2 — Execution / exchange connectivity

How orders actually reach a venue.

| Option | What it is | Fit |
|---|---|---|
| **CCXT** | Unified trading API for 100+ exchanges (Py/TS/Go/…). Spot, futures, OHLCV, order books, order placement. Free, mature. | **Default.** One code path for many CEXs. |
| **CCXT Pro** | CCXT + WebSocket streaming | When you need streaming + trading in one lib |
| **Alpaca** | Unified stocks + crypto API; routes to Coinbase/Binance; <200ms | Good if cross-asset later; broker-style |
| **Hyperliquid / DEX perps** | On-chain perps; Hyperliquid ~$1.8T/mo notional (Feb 2026) | Phase 2+ if DeFi/perps in scope |
| **Hummingbot** | Full algo-trading framework (market-making, arb), 140+ exchanges, has an MCP server | If strategies get algorithmic |
| **FalconX / institutional** | Post-trade, settlement, weekend liquidity | Out of scope for MVP |

**Recommendation:** CCXT against **one** CEX first (Coinbase or Kraken — both have
clean APIs and US-friendly posture). Prove the full loop on paper/sandbox before
real keys. Expand venues later since CCXT keeps the code identical.

---

## Layer 3 — MCP servers (the bridge between the LLM and crypto)

MCP is now the standard way to give an AI assistant crypto capabilities. The space
splits into **data-first**, **execution**, and **analytics** servers.

| MCP server | Capability | Execution? | Pricing / connect |
|---|---|---|---|
| **CoinGecko MCP** | Prices, DEX analytics, trending, metadata (15k+ coins) | No | Free tier → $999+; Claude/Cursor/ChatGPT |
| **CoinMarketCap MCP** | Real-time prices, on-chain DEX monitoring | No | Official; MCP-compatible clients |
| **CCXT MCP** | Unified exchange data + trading (spot/futures/options) | **Yes** (bring your keys) | Free, open-source |
| **Binance MCP** | Binance futures, advanced orders, leverage | **Yes** (Binance-only) | Free |
| **Hummingbot MCP** | Market-making / arb / algo strategies | **Yes** | Free, open-source |
| **altFINS MCP** | 150+ indicators, 120 signals, candlestick patterns, on-chain, execution | **Yes** (CEX + DEX aggregator) | Free → $699/mo; Claude Desktop, Perplexity |
| **DexPaprika MCP** | Liquidity pools, TVL, cross-chain (5M+ tokens, 20+ chains) | No | Free, no API key |

**Recommendation:** Use **CoinGecko MCP** (read-only data) and **CCXT MCP**
(execution) as the two servers the assistant connects to. Keeping data and
execution in separate servers makes it easy to run the assistant in a safe
read-only mode. altFINS MCP is a strong optional add for turnkey TA signals.

Trend to note: industry expects **execution-capable MCPs to be the default for
trading agents by end of 2026** — so designing around MCP execution now is
future-aligned.

---

## Layer 4 — Analysis (technical, on-chain, sentiment)

The "proper analysis to guide the trader" from the vision.

**Technical analysis**
- `pandas-ta` / TA-Lib (Python) for indicators computed locally on OHLCV.
- altFINS (via MCP) for pre-computed 150+ indicators and signals if you prefer
  not to compute in-house.

**On-chain intelligence**
- **Glassnode** — deep on-chain metrics (SOPR, NUPL), AI alerts on whale/exchange
  flows.
- **Nansen** — labeled wallets, "smart money" tracking, GPT-style natural-language
  search.
- **Santiment** — merges social sentiment with on-chain behavior in one view.
- **Dune / DeFiLlama** — custom queries and DeFi/TVL data.

**Sentiment / social**
- **LunarCrush** — real-time social intelligence across X, Reddit, TikTok,
  Telegram; token-level social momentum; positions itself as an AI co-pilot.
- **CoinMarketCap Fear & Greed Index** — cheap macro emotional gauge.
- **CoinGlass** — derivatives / funding / liquidation data.

**Recommendation:** MVP ships technical analysis computed locally (`pandas-ta`) +
Fear & Greed + LunarCrush for a sentiment tile. Add Glassnode/Nansen in phase 2
when the budget and use cases justify their cost.

---

## Layer 5 — AI / LLM assistant layer

The chat assistant that analyzes positions and can execute trades.

Landscape findings:
- **Multi-agent beats single-model.** 2026 research (BlackRock/Columbia) shows a
  three-layer Bull / Bear / Risk-Supervisor framework consistently outperforms a
  single LLM. A typical "agent fleet" has Macro, Narrative, and Execution agents.
- **ElizaOS** — most widely deployed open-source crypto agent framework; plugin
  architecture, multi-LLM. Default for DeFi-native projects.
- **Olas (Valory)** — infrastructure for autonomous on-chain agents.
- Retail-facing agentic tools: Arkham, Token Metrics, Cryptohopper.

**Recommendation for this project:** Build the assistant on **Claude (Opus 4.8)**
using the **Claude Agent SDK** with tool-use, since the project is already
Claude-native and the Agent SDK is a first-class MCP client — it can talk to the
CoinGecko + CCXT MCP servers directly. Start single-agent (chat + tools). If
signal quality demands it, evolve toward the Bull/Bear/Risk multi-agent pattern
rather than adopting a heavier crypto-specific framework up front. (Consult the
`claude-api` skill when writing the integration code.)

---

## Layer 6 — Frontend / charting (the "visually stunning workstation")

| Library | Fit | Notes |
|---|---|---|
| **TradingView Lightweight Charts** | **Primary chart engine** | Same engine as TradingView, open-source, 45KB gzipped, built for streaming OHLCV/time-series; official React tutorial |
| Apache ECharts | Secondary / richer chart types | Free (Apache-2.0), scales well |
| Recharts / Victory | Dashboard tiles, KPIs, simple series | Declarative React |
| Unovis | Modular, instant dark-mode, TS-first | Good for a themed workstation |
| D3.js | Bespoke visuals | Max control, max effort |

Well-trodden 2026 build path: **Lightweight Charts + CCXT for data + Next.js
dashboard + Postgres (Drizzle) for trade history**, fed by WebSockets for
real-time updates.

**Recommendation:** Next.js + React, Lightweight Charts for price/OHLCV, ECharts
or Recharts for auxiliary panels (depth, portfolio, sentiment). Design for
light/dark theming from day one given the "visually stunning" goal.

---

## Layer 7 — Persistence, backtesting, safety

- **Trade history / state:** Postgres (+ Drizzle or SQLAlchemy). Time-series
  extension (Timescale) optional for tick data.
- **Backtesting:** Hummingbot has it built in; otherwise `backtrader` / `vectorbt`
  in Python against historical OHLCV.
- **Safety (critical):**
  - Start on **exchange testnet / paper trading**; never wire real keys until the
    loop is proven.
  - **Human-in-the-loop confirmation on every order** the LLM proposes.
  - Read-only assistant mode by default; execution behind an explicit toggle.
  - Store API keys in a secrets manager, scope keys to trade-only (no withdrawal).
  - Rate-limit and cap order size / notional per the assistant.

---

## Recommended phased architecture (maps to incremental build)

```
Phase 1  Read-only workstation
  Next.js + Lightweight Charts  <-- WS  CoinGecko / exchange native feed
  Claude Agent SDK assistant    <-- MCP  CoinGecko MCP (data only)
  Local TA (pandas-ta) + Fear&Greed + LunarCrush tiles

Phase 2  Paper trading
  + CCXT against exchange testnet / paper account
  + CCXT MCP (execution) with human confirmation
  + Postgres trade history + backtesting

Phase 3  Live trading (gated)
  + Real API keys (trade-only scope) behind confirmation + notional caps
  + On-chain (Glassnode/Nansen) and richer multi-agent analysis
```

---

## Decisions made (2026-07-06)

1. **Target venue:** Coinbase or Kraken (US-friendly, clean APIs). Still build the
   execution layer on CCXT so the specific exchange stays swappable.
2. **Instruments:** **Spot only** for v1 — simplest execution and risk model.
   No leverage, funding, or DeFi in the first version.
3. **Platform:** **Web app (Next.js)** — fastest to build and share.

These narrow the MVP stack to: Next.js + Lightweight Charts frontend, CoinGecko
API/MCP for data, CCXT (Coinbase/Kraken, spot) for execution behind a CCXT MCP,
and a Claude Agent SDK assistant. No futures/perps/DeFi code paths in v1.

## Still open before architecture/business plan

1. **Regulatory posture:** an app that executes trades on a user's behalf may have
   licensing/compliance implications depending on whether it's for personal use
   vs distributed to others. Confirm this is single-user/personal for now.
2. **Budget:** free tiers get an MVP built; on-chain intel (Glassnode/Nansen/
   Kaiko) and higher WS tiers cost real money — defer to phase 2.
3. **Which of Coinbase vs Kraken** specifically (can decide at architecture time).

---

## Sources

- [Top 5 Crypto WebSocket APIs 2026 — CoinGecko](https://www.coingecko.com/learn/top-5-best-crypto-websocket-apis)
- [Best Crypto API for Trading Bots 2026 — CoinMarketCap](https://coinmarketcap.com/academy/article/best-crypto-api-for-trading-bots-and-algorithmic-trading-2026)
- [The 2026 guide to crypto MCP servers — Cryptohopper](https://www.cryptohopper.com/blog/the-2026-guide-to-crypto-mcp-servers-13080)
- [Ultimate Guide to Cryptocurrency MCP Servers 2026 — altFINS](https://altfins.com/knowledge-base/the-ultimate-guide-to-cryptocurrency-mcp-servers-in-2026-complete-comparison-for-traders-developers-trading-platforms/)
- [CoinGecko MCP Server docs](https://docs.coingecko.com/docs/mcp-server)
- [CoinMarketCap MCP](https://coinmarketcap.com/api/mcp/)
- [CCXT — GitHub](https://github.com/ccxt/ccxt) and [docs](https://docs.ccxt.com/)
- [mcp-server-ccxt — GitHub](https://github.com/Nayshins/mcp-server-ccxt)
- [crypto-trading-mcp — GitHub](https://github.com/vkdnjznd/crypto-trading-mcp)
- [awesome-mcp-servers: finance/crypto — TensorBlock](https://github.com/TensorBlock/awesome-mcp-servers/blob/main/docs/finance--crypto.md)
- [Top CCXT Pro Alternatives 2026 — Slashdot](https://slashdot.org/software/p/CCXT-Pro/alternatives)
- [Best Crypto Analysis Tools 2026 — Coin Bureau](https://coinbureau.com/review/crypto-research-tools)
- [Santiment](https://app.santiment.net/) · [LunarCrush](https://lunarcrush.com/) · [Glassnode](https://glassnode.com/)
- [AI Agents vs LLMs in Crypto 2026 — KuCoin](https://www.kucoin.com/blog/ai-agents-vs-llms-crypto-analysis-market-2026)
- [Top AI Agents for Crypto 2026 — Medium/Predict](https://medium.com/predict/top-ai-agents-for-crypto-in-2026-leading-trading-and-analysis-tools-165089bdc3f5)
- [Chart.js vs Lightweight Charts vs TradingView — index.dev](https://www.index.dev/skill-vs-skill/tradingview-vs-lightweight-charts-vs-chartjs)
- [Lightweight Charts — TradingView](https://www.tradingview.com/lightweight-charts/)
- [Trading Dashboard with React + WebSockets 2026 — OpenWeb Solutions](https://openwebsolutions.in/blog/high-performance-trading-dashboard-react-websockets/)
</content>
</invoke>
