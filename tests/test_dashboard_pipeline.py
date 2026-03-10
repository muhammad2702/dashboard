from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from trading_dashboard import DashboardToolkit
from trading_dashboard.core.types import MarketBar
from trading_dashboard.data.base import DataSource
from trading_dashboard.data.router import DataRouter
from trading_dashboard.signals.dsl import ExpressionIndicator
from trading_dashboard.signals.engine import SignalEngine
from trading_dashboard.ui.dashboard import DashboardLayout
from trading_dashboard.ui.widgets import AutoViewWidget
from trading_dashboard.use_cases.lqd_hyg import divergence_score, register_lqd_hyg_dashboard


class StubDataSource(DataSource):
    def __init__(self) -> None:
        self._running = False

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def subscribe_ticks(self, symbol: str):
        while self._running:
            await asyncio.sleep(0.05)
            if False:
                yield

    async def subscribe_bars(self, symbol: str, timeframe: str):
        base = 110.0 if symbol == "LQD" else 85.0
        for i in range(40):
            if not self._running:
                break
            close = base + (i * 0.1 if symbol == "LQD" else i * 0.07)
            yield MarketBar(symbol, timeframe, close, close, close, close, 1_000, datetime.now(timezone.utc))
            await asyncio.sleep(0.01)
        while self._running:
            await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_expression_indicator_updates_widget_state() -> None:
    router = DataRouter()
    engine = SignalEngine(router)
    layout = DashboardLayout()

    indicator = ExpressionIndicator(
        name="lqd-hyg-corr",
        symbols=("LQD", "HYG"),
        timeframe="1m",
        view="metric",
        compute=lambda s: {"value": s.correlation("LQD", "HYG")},
    )

    engine.register_indicator(indicator)
    engine.subscribe(layout.on_signal)
    layout.register_widget(AutoViewWidget("lqd-hyg-corr", "LQD/HYG Corr", "lqd-hyg-corr"))

    await engine.start()
    await asyncio.sleep(0.05)

    for px in [100.0, 101.0, 102.0, 103.0]:
        await router.publish_bar(MarketBar("LQD", "1m", px, px, px, px, 1000, datetime.now(timezone.utc)))
        await router.publish_bar(MarketBar("HYG", "1m", px * 0.8, px * 0.8, px * 0.8, px * 0.8, 1000, datetime.now(timezone.utc)))

    await asyncio.sleep(0.05)
    await engine.stop()

    assert "lqd-hyg-corr" in layout.state


def test_divergence_payload_schema() -> None:
    from trading_dashboard.core.frame import RollingStore

    store = RollingStore(max_points=120)
    now = datetime.now(timezone.utc)
    for i in range(100):
        store.ingest_bar(MarketBar("LQD", "1m", 110 + i * 0.05, 0, 0, 110 + i * 0.05, 1000, now))
        store.ingest_bar(MarketBar("HYG", "1m", 85 + i * 0.02, 0, 0, 85 + i * 0.02, 1000, now))

    payload = divergence_score(store.snapshot(), window=80)
    assert payload is not None
    assert payload["payload"]["view"] == "timeseries"


@pytest.mark.asyncio
async def test_toolkit_register_lqd_hyg_dashboard() -> None:
    toolkit = DashboardToolkit(data_source=StubDataSource())
    register_lqd_hyg_dashboard(toolkit)

    await toolkit.start(symbols=["LQD", "HYG"])
    await asyncio.sleep(1.0)
    await toolkit.stop()

    state = toolkit.layout.state
    assert "lqd-hyg-correlation" in state
    assert "lqd-hyg-divergence" in state
