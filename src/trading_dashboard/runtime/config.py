from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class RuntimeConfig:
    ibkr_host: str = "127.0.0.1"
    ibkr_port: int = 7496
    ibkr_client_id: int = 7
    renderer: str = "streamlit"
    timeframe: str = "1m"
    modules: tuple[str, ...] = ("credit_canary",)
    dynamic_modules: tuple[str, ...] = ()

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        modules_raw = os.getenv("TD_MODULES", "credit_canary")
        modules = tuple(part.strip() for part in modules_raw.split(",") if part.strip())
        dyn_raw = os.getenv("TD_DYNAMIC_MODULES", "")
        dynamic_modules = tuple(part.strip() for part in dyn_raw.split(",") if part.strip())
        return cls(
            ibkr_host=os.getenv("TD_IBKR_HOST", "127.0.0.1"),
            ibkr_port=int(os.getenv("TD_IBKR_PORT", "7496")),
            ibkr_client_id=int(os.getenv("TD_IBKR_CLIENT_ID", "7")),
            renderer=os.getenv("TD_RENDERER", "streamlit"),
            timeframe=os.getenv("TD_TIMEFRAME", "1m"),
            modules=modules,
            dynamic_modules=dynamic_modules,
        )
