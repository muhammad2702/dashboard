from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from trading_dashboard.core.types import MarketBar, MarketTick
from trading_dashboard.data.base import DataSource

_IBKR_AVAILABLE = True
try:
    from ib_insync import Contract, IB, RealTimeBar, Ticker
except ImportError:  # optional dependency
    _IBKR_AVAILABLE = False
    IB = Any  # type: ignore
    Contract = Any  # type: ignore
    Ticker = Any  # type: ignore
    RealTimeBar = Any  # type: ignore


class IBKRDataSource(DataSource):
    """IBKR implementation for tick and bar streams via ib_insync."""

    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 7) -> None:
        self.host = host
        self.port = port
        self.client_id = client_id
        self._ib: IB | None = None

    async def start(self) -> None:
        if not _IBKR_AVAILABLE:
            raise RuntimeError("ib-insync is required for IBKRDataSource. Install with: pip install .[ibkr]")
        self._ib = IB()
        await self._ib.connectAsync(self.host, self.port, clientId=self.client_id)

    async def stop(self) -> None:
        if self._ib:
            self._ib.disconnect()
            self._ib = None

    async def subscribe_ticks(self, symbol: str):
        if not self._ib:
            raise RuntimeError("Data source must be started before subscribing.")
        contract = Contract(symbol=symbol, secType="STK", exchange="SMART", currency="USD")
        ticker: Ticker = self._ib.reqMktData(contract, "", False, False)

        queue: asyncio.Queue[MarketTick] = asyncio.Queue(maxsize=1000)

        def on_update(updated: Ticker) -> None:
            if updated.last is None:
                return
            tick = MarketTick(
                symbol=symbol,
                price=float(updated.last),
                size=float(updated.lastSize or 0),
                timestamp=datetime.now(timezone.utc),
                venue=updated.exchange,
            )
            if not queue.full():
                queue.put_nowait(tick)

        ticker.updateEvent += on_update
        try:
            while True:
                yield await queue.get()
        finally:
            ticker.updateEvent -= on_update
            self._ib.cancelMktData(contract)

    async def subscribe_bars(self, symbol: str, timeframe: str):
        if not self._ib:
            raise RuntimeError("Data source must be started before subscribing.")
        contract = Contract(symbol=symbol, secType="STK", exchange="SMART", currency="USD")
        bars = self._ib.reqRealTimeBars(contract, barSize=5, whatToShow="TRADES", useRTH=False)

        queue: asyncio.Queue[MarketBar] = asyncio.Queue(maxsize=1000)

        def on_bar(_: list[RealTimeBar], has_new_bar: bool) -> None:
            if not has_new_bar:
                return
            bar = bars[-1]
            normalized = MarketBar(
                symbol=symbol,
                timeframe=timeframe,
                open=float(bar.open_),
                high=float(bar.high),
                low=float(bar.low),
                close=float(bar.close),
                volume=float(bar.volume),
                timestamp=datetime.fromtimestamp(bar.time, tz=timezone.utc),
            )
            if not queue.full():
                queue.put_nowait(normalized)

        bars.updateEvent += on_bar
        try:
            while True:
                yield await queue.get()
        finally:
            bars.updateEvent -= on_bar
            self._ib.cancelRealTimeBars(bars)
