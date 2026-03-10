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
        self._tasks_by_key: dict[tuple[str, str], tuple[asyncio.Task[None], asyncio.Task[None]]] = {}
        self._grouped: dict[tuple[str, str], list[Indicator]] = defaultdict(list)
        self._running = False

    def register_indicator(self, indicator: Indicator) -> None:
        self._indicators.append(indicator)
        for symbol in indicator.symbols:
            key = (symbol, indicator.timeframe)
            self._grouped[key].append(indicator)
            if self._running and key not in self._tasks_by_key:
                tick_task = asyncio.create_task(self._drive_ticks(symbol, key))
                bar_task = asyncio.create_task(self._drive_bars(symbol, indicator.timeframe, key))
                self._tasks_by_key[key] = (tick_task, bar_task)

    def subscribe(self, sink: SignalSink) -> None:
        self._subscribers.append(sink)

    async def start(self) -> None:
        self._running = True
        for key in self._grouped:
            if key in self._tasks_by_key:
                continue
            symbol, timeframe = key
            tick_task = asyncio.create_task(self._drive_ticks(symbol, key))
            bar_task = asyncio.create_task(self._drive_bars(symbol, timeframe, key))
            self._tasks_by_key[key] = (tick_task, bar_task)

    async def stop(self) -> None:
        self._running = False
        tasks: list[asyncio.Task[None]] = []
        for pair in self._tasks_by_key.values():
            tasks.extend(pair)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks_by_key.clear()

    async def _emit(self, signal: SignalPoint) -> None:
        await asyncio.gather(*(subscriber(signal) for subscriber in self._subscribers))

    async def _drive_ticks(self, symbol: str, key: tuple[str, str]) -> None:
        async for tick in self.router.subscribe_ticks(symbol):
            await self._dispatch_tick(tick, self._grouped[key])

    async def _drive_bars(self, symbol: str, timeframe: str, key: tuple[str, str]) -> None:
        async for bar in self.router.subscribe_bars(symbol, timeframe):
            await self._dispatch_bar(bar, self._grouped[key])

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
