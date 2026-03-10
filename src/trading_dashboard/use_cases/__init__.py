"""Prebuilt analytical dashboard modules."""

from trading_dashboard.use_cases.base import AnalysisSpec, RuntimeModule, WidgetSpec
from trading_dashboard.use_cases.lqd_hyg import CreditCanaryModule, register_lqd_hyg_dashboard
from trading_dashboard.use_cases.market_toolkits import CrossAssetRegimeModule

__all__ = [
    "AnalysisSpec",
    "CreditCanaryModule",
    "CrossAssetRegimeModule",
    "RuntimeModule",
    "WidgetSpec",
    "register_lqd_hyg_dashboard",
]
