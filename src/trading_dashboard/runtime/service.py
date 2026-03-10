from __future__ import annotations

import asyncio

from trading_dashboard import DashboardToolkit
from trading_dashboard.data.ibkr import IBKRDataSource
from trading_dashboard.runtime.config import RuntimeConfig
from trading_dashboard.runtime.module_registry import build_modules
from trading_dashboard.ui.qt_terminal import run_qt_terminal
from trading_dashboard.ui.streamlit_app import run_streamlit_dashboard


class TerminalService:
    """Production runtime service for live IBKR terminal execution."""

    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self.toolkit = DashboardToolkit(
            data_source=IBKRDataSource(
                host=config.ibkr_host,
                port=config.ibkr_port,
                client_id=config.ibkr_client_id,
            )
        )
        for module in build_modules(config.modules, config.dynamic_modules):
            self.toolkit.install_module(module)

    async def run(self) -> None:
        await self.toolkit.start(timeframe=self.config.timeframe)
        try:
            if self.config.renderer == "qt":
                run_qt_terminal(self.toolkit.layout)
            else:
                while True:
                    run_streamlit_dashboard(self.toolkit.layout.state, workspace=self.toolkit.layout.workspace)
                    await asyncio.sleep(1.0)
        finally:
            await self.toolkit.stop()
