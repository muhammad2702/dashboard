from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from trading_dashboard import DashboardToolkit
from trading_dashboard.core.types import MarketBar
from trading_dashboard.data.mock import MockDataSource
from trading_dashboard.data.router import DataRouter
from trading_dashboard.signals.dsl import ExpressionIndicator
from trading_dashboard.signals.engine import SignalEngine
from trading_dashboard.ui.dashboard import DashboardLayout
from trading_dashboard.ui.widgets import AutoViewWidget


@pytest.mark.asyncio
async def test_expression_indicator_updates_widget_state() -> None:
    router = DataRouter()
    engine = SignalEngine(router)
    layout = DashboardLayout()

    indicator = ExpressionIndicator(
        name="pair-corr",
        symbols=("AAPL", "MSFT"),
        timeframe="1m",
        view="metric",
        compute=lambda s: {"value": s.correlation("AAPL", "MSFT")},
    )

    engine.register_indicator(indicator)
    engine.subscribe(layout.on_signal)
    layout.register_widget(AutoViewWidget("pair-corr", "Pair Corr", "pair-corr"))

    await engine.start()
    await asyncio.sleep(0.05)

    for px in [100.0, 101.0, 102.0]:
        await router.publish_bar(
            MarketBar("AAPL", "1m", px, px, px, px, 1000, datetime.now(timezone.utc))
        )
        await router.publish_bar(
            MarketBar("MSFT", "1m", px * 2, px * 2, px * 2, px * 2, 1000, datetime.now(timezone.utc))
        )

    await asyncio.sleep(0.05)
    await engine.stop()

    assert "pair-corr" in layout.state
    assert layout.state["pair-corr"].payload["view"] == "metric"


def test_workspace_detach_attach() -> None:
    layout = DashboardLayout()
    layout.register_widget(AutoViewWidget("spread", "Spread", "spread", view="metric"))

    layout.workspace.detach("spread")
    assert layout.workspace.snapshot()["spread"].detached is True

    layout.workspace.attach("spread")
    assert layout.workspace.snapshot()["spread"].detached is False


@pytest.mark.asyncio
async def test_toolkit_one_line_logic_registration() -> None:
    toolkit = DashboardToolkit(data_source=MockDataSource())
    toolkit.add_logic(
        "spread",
        ("AAPL", "MSFT"),
        lambda s: {"value": (s.latest_bar("AAPL").close - s.latest_bar("MSFT").close)}
        if s.latest_bar("AAPL") and s.latest_bar("MSFT")
        else None,
    )

    await toolkit.start(symbols=["AAPL", "MSFT"])
    await asyncio.sleep(1.5)
    await toolkit.stop()

    assert "spread" in toolkit.layout.state
