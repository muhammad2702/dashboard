from __future__ import annotations

import os

from trading_dashboard import DashboardToolkit
from trading_dashboard.data.ibkr import IBKRDataSource
from trading_dashboard.runtime import MODULE_REGISTRY, RuntimeConfig, build_modules
from trading_dashboard.use_cases import AnalysisSpec, CreditCanaryModule, CrossAssetRegimeModule, WidgetSpec


class DynamicTestModule:
    name = "dynamic-test"
    symbols = ("SPY",)

    def analyses(self) -> list[AnalysisSpec]:
        return [
            AnalysisSpec(
                name="spy-last",
                symbols=("SPY",),
                compute=lambda s: {"value": (s.latest_bar("SPY").close if s.latest_bar("SPY") else 0.0)},
                widget=WidgetSpec(title="SPY Last", view="metric", width=500, height=260),
            )
        ]


def test_ibkr_default_port_is_live_gateway_port() -> None:
    ds = IBKRDataSource()
    assert ds.port == 7496


def test_runtime_config_defaults() -> None:
    original = os.environ.pop("TD_DYNAMIC_MODULES", None)
    try:
        cfg = RuntimeConfig.from_env()
        assert cfg.modules == ("credit_canary",)
        assert cfg.dynamic_modules == ()
    finally:
        if original is not None:
            os.environ["TD_DYNAMIC_MODULES"] = original


def test_module_registry_and_dynamic_loader() -> None:
    assert "credit_canary" in MODULE_REGISTRY
    modules = build_modules(("credit_canary",), ("trading_dashboard.use_cases.market_toolkits:CrossAssetRegimeModule",))
    assert len(modules) == 2


def test_framework_installs_modules_and_widget_size_contract() -> None:
    toolkit = DashboardToolkit(data_source=IBKRDataSource())
    toolkit.install_module(CreditCanaryModule())
    toolkit.install_module(CrossAssetRegimeModule())
    toolkit.install_module(DynamicTestModule())

    widget_ids = {widget.widget_id for widget in toolkit.layout.widgets}
    assert {"lqd-hyg-correlation", "rates-pressure", "spy-last"}.issubset(widget_ids)

    ws = toolkit.layout.workspace.snapshot()
    assert ws["spy-last"].w == 500
    assert ws["spy-last"].h == 260
    assert {"LQD", "HYG", "SPY", "QQQ", "TLT"}.issubset(set(toolkit.required_symbols))
