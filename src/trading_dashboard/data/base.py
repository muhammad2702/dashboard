from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from trading_dashboard.core.types import MarketBar, MarketTick


class DataSource(ABC):
    """Abstract market data source (IBKR by default, but replaceable)."""

    @abstractmethod
    async def start(self) -> None:
        """Open connections and initialize subscriptions."""

    @abstractmethod
    async def stop(self) -> None:
        """Close all connections and release resources."""

    @abstractmethod
    async def subscribe_ticks(self, symbol: str) -> AsyncIterator[MarketTick]:
        """Yield real-time ticks for a symbol."""

    @abstractmethod
    async def subscribe_bars(self, symbol: str, timeframe: str) -> AsyncIterator[MarketBar]:
        """Yield OHLCV bars for a symbol/timeframe pair."""
