from __future__ import annotations

import asyncio

from trading_dashboard.runtime.config import RuntimeConfig
from trading_dashboard.runtime.service import TerminalService


def main() -> None:
    config = RuntimeConfig.from_env()
    service = TerminalService(config)
    asyncio.run(service.run())
