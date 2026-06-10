"""
Smoke test — runs against real APIs if keys are set, mock otherwise.
Usage: python scripts/smoke_test_providers.py

Set in .env:
  ALPACA_API_KEY, ALPACA_API_SECRET → real Alpaca bars + quotes
  FINNHUB_API_KEY                   → real news + indicators
  MOCK_MODE=true                    → force mock
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.services.data_providers import (
    get_market_provider,
    get_news_provider,
    get_indicator_provider,
)

SYMBOL = "AAPL"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def ok(msg): print(f"{GREEN}✓{RESET} {msg}")
def fail(msg): print(f"{RED}✗{RESET} {msg}")


async def run():
    print(f"\nSwingScope Provider Smoke Test — symbol: {SYMBOL}\n")

    # ── Market data ──────────────────────────────────────────────────
    mp = get_market_provider()
    bars = await mp.get_bars(SYMBOL, limit=10)
    if bars:
        b = bars[-1]
        ok(f"get_bars: {len(bars)} bars, latest close=${b.close} on {b.date} [{b.source}]")
    else:
        fail("get_bars: no data returned")

    quotes = await mp.get_quotes([SYMBOL, "NVDA"])
    if quotes:
        q = quotes.get(SYMBOL)
        ok(f"get_quotes: {SYMBOL} bid={q.bid} ask={q.ask} [{q.source}]" if q else f"get_quotes: no quote for {SYMBOL}")
    else:
        fail("get_quotes: empty")

    # ── News ─────────────────────────────────────────────────────────
    np_ = get_news_provider()
    news = await np_.get_news(SYMBOL, limit=3)
    if news:
        ok(f"get_news: {len(news)} items, headline='{news[0].headline[:60]}...' [{news[0].source}]")
    else:
        fail("get_news: no items returned")

    sentiment = await np_.get_sentiment(SYMBOL)
    if sentiment is not None:
        ok(f"get_sentiment: {sentiment:.4f} (positive > 0)")
    else:
        fail("get_sentiment: None returned")

    # ── Indicators ───────────────────────────────────────────────────
    ip = get_indicator_provider()
    rsi = await ip.get_indicator(SYMBOL, "RSI")
    if rsi:
        ok(f"get_indicator RSI: {rsi.value:.2f} [{rsi.source}]")
    else:
        fail("get_indicator RSI: None returned")

    print()


if __name__ == "__main__":
    asyncio.run(run())
