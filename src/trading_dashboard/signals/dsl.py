from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from trading_dashboard.core.frame import LogicSnapshot, RollingStore
from trading_dashboard.core.types import MarketBar, MarketTick, SignalPoint
from trading_dashboard.signals.base import Indicator

ComputeFunc = Callable[[LogicSnapshot], Any]


class ExpressionIndicator(Indicator):
    """Indicator that runs a plain function against a rolling market snapshot."""

    def __init__(
        self,
        name: str,
        symbols: tuple[str, ...],
        timeframe: str,
        compute: ComputeFunc,
        view: str = "metric",
        lookback: int = 500,
        trigger: str = "bar",
    ) -> None:
        self.name = name
        self.symbols = symbols
        self.timeframe = timeframe
        self.compute = compute
        self.view = view
        self.trigger = trigger
        self.store = RollingStore(max_points=lookback)

    async def on_tick(self, tick: MarketTick) -> SignalPoint | None:
        self.store.ingest_tick(tick)
        if self.trigger != "tick":
            return None
        return self._evaluate(default_symbol=tick.symbol)

    async def on_bar(self, bar: MarketBar) -> SignalPoint | None:
        self.store.ingest_bar(bar)
        if self.trigger != "bar":
            return None
        return self._evaluate(default_symbol=bar.symbol)

    def _evaluate(self, default_symbol: str) -> SignalPoint | None:
        snapshot = self.store.snapshot()
        result = self.compute(snapshot)
        if result is None:
            return None

        value = 0.0
        confidence = 1.0
        payload: dict[str, Any] = {}

        if isinstance(result, (int, float)):
            value = float(result)
            payload = {"value": value}
        elif isinstance(result, dict):
            value = float(result.get("value", 0.0))
            confidence = float(result.get("confidence", 1.0))
            payload = result.get("payload", result)
        else:
            payload = {"value": str(result)}

        return SignalPoint(
            name=self.name,
            symbol=default_symbol,
            value=value,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc),
            metadata={"view": self.view, "payload": payload},
        )
