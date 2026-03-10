from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable

from trading_dashboard.core.types import MarketBar, MarketTick, SignalPoint
from trading_dashboard.data.router import DataRouter
from trading_dashboard.signals.base import Indicator

SignalSink = Callable[[SignalPoint], Awaitable[None]]


class SignalEngine:
    def __init__(self, router: DataRouter) -> None:
        self.router = router
        self._indicators: list[Indicator] = []
        self._subscribers: list[SignalSink] = []
        self._tasks: list[asyncio.Task[None]] = []

    def register_indicator(self, indicator: Indicator) -> None:
        self._indicators.append(indicator)

    def subscribe(self, sink: SignalSink) -> None:
        self._subscribers.append(sink)

    async def start(self) -> None:
        grouped: dict[tuple[str, str], list[Indicator]] = defaultdict(list)
        for indicator in self._indicators:
            for symbol in indicator.symbols:
                grouped[(symbol, indicator.timeframe)].append(indicator)

        for (symbol, timeframe), indicators in grouped.items():
            self._tasks.append(asyncio.create_task(self._drive_ticks(symbol, indicators)))
            self._tasks.append(asyncio.create_task(self._drive_bars(symbol, timeframe, indicators)))

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _emit(self, signal: SignalPoint) -> None:
        await asyncio.gather(*(subscriber(signal) for subscriber in self._subscribers))

    async def _drive_ticks(self, symbol: str, indicators: list[Indicator]) -> None:
        async for tick in self.router.subscribe_ticks(symbol):
            await self._dispatch_tick(tick, indicators)

    async def _drive_bars(self, symbol: str, timeframe: str, indicators: list[Indicator]) -> None:
        async for bar in self.router.subscribe_bars(symbol, timeframe):
            await self._dispatch_bar(bar, indicators)

    async def _dispatch_tick(self, tick: MarketTick, indicators: list[Indicator]) -> None:
        for indicator in indicators:
            signal = await indicator.on_tick(tick)
            if signal is not None:
                await self._emit(signal)

    async def _dispatch_bar(self, bar: MarketBar, indicators: list[Indicator]) -> None:
        for indicator in indicators:
            signal = await indicator.on_bar(bar)
            if signal is not None:
                await self._emit(signal)
