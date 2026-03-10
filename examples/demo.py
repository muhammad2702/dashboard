from __future__ import annotations

import asyncio

from trading_dashboard import DashboardToolkit
from trading_dashboard.data.ibkr import IBKRDataSource
from trading_dashboard.ui.qt_terminal import run_qt_terminal
from trading_dashboard.ui.streamlit_app import run_streamlit_dashboard
from trading_dashboard.use_cases.lqd_hyg import register_lqd_hyg_dashboard


async def main(renderer: str = "streamlit") -> None:
    toolkit = DashboardToolkit(data_source=IBKRDataSource(port=7496))
    register_lqd_hyg_dashboard(toolkit)

    await toolkit.start(symbols=["LQD", "HYG"])
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
