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
from trading_dashboard.use_cases.base import AnalysisSpec


class DashboardToolkit:
    """Composes data source, signal engine, and detachable dashboard windows."""

    def __init__(self, data_source: DataSource) -> None:
        self.data_source = data_source
        self.router = DataRouter()
        self.layout = DashboardLayout()
        self.engine = SignalEngine(self.router)
        self._pump_tasks: dict[str, tuple[asyncio.Task[None], asyncio.Task[None]]] = {}
        self._module_symbols: set[str] = set()
        self._running = False
        self._timeframe = "1m"

    def add_indicator(self, indicator: Indicator) -> None:
        self.engine.register_indicator(indicator)

    def add_widget(self, widget: DashboardWidget) -> None:
        self.layout.register_widget(widget)

    def install_module(self, module: Any) -> None:
        """Register a runtime module; supports both analyses() interface and legacy register()."""
        if hasattr(module, "analyses"):
            for spec in module.analyses():
                self.add_analysis(spec)
        else:
            symbols = getattr(module, "symbols", ())
            self._module_symbols.update(symbols)
            module.register(self)

    @property
    def required_symbols(self) -> list[str]:
        return sorted(self._module_symbols)

    def add_analysis(self, spec: AnalysisSpec) -> None:
        self.add_logic(
            name=spec.name,
            symbols=spec.symbols,
            compute=spec.compute,
            title=spec.widget.title,
            timeframe=spec.timeframe,
            view=spec.widget.view,
            lookback=spec.lookback,
            trigger=spec.trigger,
            width=spec.widget.width,
            height=spec.widget.height,
        )

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
        width: int = 420,
        height: int = 280,
    ) -> None:
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
        self.add_widget(
            AutoViewWidget(widget_id=name, title=title or name, signal_name=name, view=view, width=width, height=height)
        )
        new_symbols = set(symbols) - self._module_symbols
        self._module_symbols.update(symbols)
        if self._running:
            for symbol in new_symbols:
                self._ensure_symbol_pumps(symbol, self._timeframe)

    async def start(self, symbols: list[str] | None = None, timeframe: str = "1m") -> None:
        active_symbols = symbols or self.required_symbols
        self._timeframe = timeframe
        await self.data_source.start()
        self.engine.subscribe(self.layout.on_signal)
        await self.engine.start()
        self._running = True

        for symbol in active_symbols:
            self._ensure_symbol_pumps(symbol, timeframe)

    async def stop(self) -> None:
        self._running = False
        tasks: list[asyncio.Task[None]] = []
        for pair in self._pump_tasks.values():
            tasks.extend(pair)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._pump_tasks.clear()
        await self.engine.stop()
        await self.data_source.stop()

    def _ensure_symbol_pumps(self, symbol: str, timeframe: str) -> None:
        if symbol in self._pump_tasks:
            return
        tick_task = asyncio.create_task(self._pump_ticks(symbol))
        bar_task = asyncio.create_task(self._pump_bars(symbol, timeframe))
        self._pump_tasks[symbol] = (tick_task, bar_task)

    async def _pump_ticks(self, symbol: str) -> None:
        async for tick in self.data_source.subscribe_ticks(symbol):
            await self.router.publish_tick(tick)

    async def _pump_bars(self, symbol: str, timeframe: str) -> None:
        async for bar in self.data_source.subscribe_bars(symbol, timeframe):
            await self.router.publish_bar(bar)
