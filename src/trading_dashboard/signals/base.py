from __future__ import annotations

from abc import ABC

from trading_dashboard.core.types import MarketBar, MarketTick, SignalPoint


class Indicator(ABC):
    """Implement only signal logic; framework handles data plumbing + rendering."""

    name: str = "indicator"
    symbols: tuple[str, ...] = ()
    timeframe: str = "1m"

    async def on_tick(self, tick: MarketTick) -> SignalPoint | None:
        return None

    async def on_bar(self, bar: MarketBar) -> SignalPoint | None:
        return None
