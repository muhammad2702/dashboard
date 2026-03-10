from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from trading_dashboard.core.frame import LogicSnapshot
from trading_dashboard.data.base import DataSource
from trading_dashboard.data.router import DataRouter
from trading_dashboard.signals.base import Indicator
from trading_dashboard.signals.dsl import ExpressionIndicator
from trading_dashboard.signals.engine import SignalEngine
from trading_dashboard.ui.dashboard import DashboardLayout
from trading_dashboard.ui.widgets import AutoViewWidget, DashboardWidget


class DashboardToolkit:
    """Composes data source, signal engine, and detachable dashboard windows."""

    def __init__(self, data_source: DataSource) -> None:
        self.data_source = data_source
        self.router = DataRouter()
        self.layout = DashboardLayout()
        self.engine = SignalEngine(self.router)
        self._pump_tasks: list[asyncio.Task[None]] = []

    def add_indicator(self, indicator: Indicator) -> None:
        self.engine.register_indicator(indicator)

    def add_widget(self, widget: DashboardWidget) -> None:
        self.layout.register_widget(widget)

    def add_logic(
        self,
        name: str,
        symbols: tuple[str, ...],
        compute: Callable[[LogicSnapshot], Any],
        *,
        title: str | None = None,
        timeframe: str = "1m",
        view: str = "metric",
        lookback: int = 500,
        trigger: str = "bar",
    ) -> None:
        """One-call registration: data subscription + logic + rendering widget."""
        indicator = ExpressionIndicator(
            name=name,
            symbols=symbols,
            timeframe=timeframe,
            compute=compute,
            view=view,
            lookback=lookback,
            trigger=trigger,
        )
        self.add_indicator(indicator)
        self.add_widget(AutoViewWidget(widget_id=name, title=title or name, signal_name=name, view=view))

    async def start(self, symbols: list[str], timeframe: str = "1m") -> None:
        await self.data_source.start()
        self.engine.subscribe(self.layout.on_signal)
        await self.engine.start()

        for symbol in symbols:
            self._pump_tasks.append(asyncio.create_task(self._pump_ticks(symbol)))
            self._pump_tasks.append(asyncio.create_task(self._pump_bars(symbol, timeframe)))

    async def stop(self) -> None:
        for task in self._pump_tasks:
            task.cancel()
        await asyncio.gather(*self._pump_tasks, return_exceptions=True)
        self._pump_tasks.clear()
        await self.engine.stop()
        await self.data_source.stop()

    async def _pump_ticks(self, symbol: str) -> None:
        async for tick in self.data_source.subscribe_ticks(symbol):
            await self.router.publish_tick(tick)

    async def _pump_bars(self, symbol: str, timeframe: str) -> None:
        async for bar in self.data_source.subscribe_bars(symbol, timeframe):
            await self.router.publish_bar(bar)
