from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from trading_dashboard.core.types import MarketBar, MarketTick


@dataclass(slots=True)
class LogicSnapshot:
    """Read-only view of rolling market history for logic functions."""

    ticks: dict[str, list[MarketTick]]
    bars: dict[str, list[MarketBar]]

    def latest_bar(self, symbol: str) -> MarketBar | None:
        series = self.bars.get(symbol, [])
        return series[-1] if series else None

    def latest_tick(self, symbol: str) -> MarketTick | None:
        series = self.ticks.get(symbol, [])
        return series[-1] if series else None

    def closes(self, symbol: str, window: int | None = None) -> list[float]:
        series = self.bars.get(symbol, [])
        values = [bar.close for bar in series]
        return values[-window:] if window else values

    def correlation(self, left: str, right: str, window: int = 50) -> float:
        x = self.closes(left, window)
        y = self.closes(right, window)
        n = min(len(x), len(y))
        if n < 2:
            return 0.0
        x = x[-n:]
        y = y[-n:]
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        cov = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y))
        x_var = sum((a - x_mean) ** 2 for a in x)
        y_var = sum((b - y_mean) ** 2 for b in y)
        denom = (x_var * y_var) ** 0.5
        return cov / denom if denom else 0.0


class RollingStore:
    def __init__(self, max_points: int = 500) -> None:
        self.max_points = max_points
        self._ticks: dict[str, deque[MarketTick]] = {}
        self._bars: dict[str, deque[MarketBar]] = {}

    def ingest_tick(self, tick: MarketTick) -> None:
        self._ticks.setdefault(tick.symbol, deque(maxlen=self.max_points)).append(tick)

    def ingest_bar(self, bar: MarketBar) -> None:
        self._bars.setdefault(bar.symbol, deque(maxlen=self.max_points)).append(bar)

    def snapshot(self) -> LogicSnapshot:
        return LogicSnapshot(
            ticks={symbol: list(values) for symbol, values in self._ticks.items()},
            bars={symbol: list(values) for symbol, values in self._bars.items()},
        )
