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


def _timeframe_to_seconds(timeframe: str) -> int:
    unit = timeframe[-1].lower()
    value = int(timeframe[:-1])
    if unit == "s":
        return value
    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 3600
    raise ValueError(f"Unsupported timeframe '{timeframe}'. Use s/m/h suffix.")


class IBKRDataSource(DataSource):
    """IBKR implementation for tick and bar streams via ib_insync."""

    def __init__(self, host: str = "127.0.0.1", port: int = 7496, client_id: int = 7) -> None:
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

        bucket_seconds = max(_timeframe_to_seconds(timeframe), 5)
        contract = Contract(symbol=symbol, secType="STK", exchange="SMART", currency="USD")
        bars = self._ib.reqRealTimeBars(contract, barSize=5, whatToShow="TRADES", useRTH=False)

        queue: asyncio.Queue[MarketBar] = asyncio.Queue(maxsize=1000)
        bucket: dict[str, float | int] = {}

        def flush_bucket(ts: datetime) -> None:
            if not bucket:
                return
            normalized = MarketBar(
                symbol=symbol,
                timeframe=timeframe,
                open=float(bucket["open"]),
                high=float(bucket["high"]),
                low=float(bucket["low"]),
                close=float(bucket["close"]),
                volume=float(bucket["volume"]),
                timestamp=ts,
            )
            if not queue.full():
                queue.put_nowait(normalized)

        def on_bar(_: list[RealTimeBar], has_new_bar: bool) -> None:
            if not has_new_bar:
                return
            bar = bars[-1]
            ts = datetime.fromtimestamp(bar.time, tz=timezone.utc)
            bar_open = float(bar.open_)
            bar_high = float(bar.high)
            bar_low = float(bar.low)
            bar_close = float(bar.close)
            bar_volume = float(bar.volume)

            period_key = int(bar.time // bucket_seconds)
            if bucket and int(bucket["period_key"]) != period_key:
                flush_bucket(ts)
                bucket.clear()

            if not bucket:
                bucket.update(
                    {
                        "period_key": period_key,
                        "open": bar_open,
                        "high": bar_high,
                        "low": bar_low,
                        "close": bar_close,
                        "volume": bar_volume,
                    }
                )
                return

            bucket["high"] = max(float(bucket["high"]), bar_high)
            bucket["low"] = min(float(bucket["low"]), bar_low)
            bucket["close"] = bar_close
            bucket["volume"] = float(bucket["volume"]) + bar_volume

        bars.updateEvent += on_bar
        try:
            while True:
                yield await queue.get()
        finally:
            bars.updateEvent -= on_bar
            self._ib.cancelRealTimeBars(bars)
