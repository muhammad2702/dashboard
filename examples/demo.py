from __future__ import annotations

import asyncio

from trading_dashboard import DashboardToolkit
from trading_dashboard.data.mock import MockDataSource
from trading_dashboard.ui.qt_terminal import run_qt_terminal
from trading_dashboard.ui.streamlit_app import run_streamlit_dashboard


def pair_correlation(snapshot):
    corr = snapshot.correlation("AAPL", "MSFT", window=40)
    return {
        "value": corr,
        "confidence": min(abs(corr), 1.0),
        "payload": {
            "value": corr,
            "symbol": "AAPL/MSFT",
            "matrix": [[1.0, corr], [corr, 1.0]],
            "labels": ["AAPL", "MSFT"],
            "view": "matrix",
        },
    }


def spread_metric(snapshot):
    left = snapshot.latest_bar("AAPL")
    right = snapshot.latest_bar("MSFT")
    if not left or not right:
        return None
    spread = left.close - right.close
    return {"value": spread, "payload": {"value": spread, "symbol": "AAPL-MSFT", "view": "metric"}}


async def main(renderer: str = "streamlit") -> None:
    toolkit = DashboardToolkit(data_source=MockDataSource())

    # One-line registration per custom idea: data wiring + rendering are automatic.
    toolkit.add_logic("pair-corr", ("AAPL", "MSFT"), pair_correlation, title="Pair Correlation", view="matrix")
    toolkit.add_logic("spread", ("AAPL", "MSFT"), spread_metric, title="Spread")

    await toolkit.start(symbols=["AAPL", "MSFT", "NVDA"])
    try:
        if renderer == "qt":
            run_qt_terminal(toolkit.layout)
        else:
            while True:
                run_streamlit_dashboard(toolkit.layout.state, workspace=toolkit.layout.workspace)
                await asyncio.sleep(1.0)
    finally:
        await toolkit.stop()


if __name__ == "__main__":
    asyncio.run(main())
