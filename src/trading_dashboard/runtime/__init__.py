"""Runtime bootstrap and module registry."""

from trading_dashboard.runtime.config import RuntimeConfig
from trading_dashboard.runtime.module_registry import MODULE_REGISTRY, build_modules
from trading_dashboard.runtime.service import TerminalService

__all__ = ["MODULE_REGISTRY", "RuntimeConfig", "TerminalService", "build_modules"]
