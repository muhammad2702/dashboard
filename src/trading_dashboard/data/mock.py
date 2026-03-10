from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone

from trading_dashboard.core.types import MarketBar, MarketTick
from trading_dashboard.data.base import DataSource


class MockDataSource(DataSource):
    """Synthetic feed for local development and UI prototyping."""

    def __init__(self) -> None:
        self._running = False
        self._prices: dict[str, float] = {}

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def subscribe_ticks(self, symbol: str):
        self._prices.setdefault(symbol, 100.0)
        while self._running:
            move = random.uniform(-0.35, 0.35)
            self._prices[symbol] += move
            yield MarketTick(
                symbol=symbol,
                price=round(self._prices[symbol], 2),
                size=random.randint(1, 50),
                timestamp=datetime.now(timezone.utc),
                venue="SIM",
            )
            await asyncio.sleep(0.25)

    async def subscribe_bars(self, symbol: str, timeframe: str):
        self._prices.setdefault(symbol, 100.0)
        while self._running:
            open_ = self._prices[symbol]
            high = open_ + random.uniform(0, 1.2)
            low = open_ - random.uniform(0, 1.2)
            close = random.uniform(low, high)
            self._prices[symbol] = close
            yield MarketBar(
                symbol=symbol,
                timeframe=timeframe,
                open=round(open_, 2),
                high=round(high, 2),
                low=round(low, 2),
                close=round(close, 2),
                volume=random.randint(1_000, 100_000),
                timestamp=datetime.now(timezone.utc),
            )
            await asyncio.sleep(1.0)
