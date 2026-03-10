from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator

from trading_dashboard.core.types import MarketBar, MarketTick


class DataRouter:
    """Fan-out stream that decouples data ingestion from strategy consumers."""

    def __init__(self) -> None:
        self._tick_queues: dict[str, list[asyncio.Queue[MarketTick]]] = defaultdict(list)
        self._bar_queues: dict[tuple[str, str], list[asyncio.Queue[MarketBar]]] = defaultdict(list)

    async def publish_tick(self, tick: MarketTick) -> None:
        for queue in list(self._tick_queues[tick.symbol]):
            await queue.put(tick)

    async def publish_bar(self, bar: MarketBar) -> None:
        key = (bar.symbol, bar.timeframe)
        for queue in list(self._bar_queues[key]):
            await queue.put(bar)

    async def subscribe_ticks(self, symbol: str) -> AsyncIterator[MarketTick]:
        queue: asyncio.Queue[MarketTick] = asyncio.Queue(maxsize=1000)
        self._tick_queues[symbol].append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._tick_queues[symbol].remove(queue)

    async def subscribe_bars(self, symbol: str, timeframe: str) -> AsyncIterator[MarketBar]:
        key = (symbol, timeframe)
        queue: asyncio.Queue[MarketBar] = asyncio.Queue(maxsize=1000)
        self._bar_queues[key].append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._bar_queues[key].remove(queue)
