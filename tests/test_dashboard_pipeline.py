from __future__ import annotations

from trading_dashboard import DashboardToolkit
from trading_dashboard.data.ibkr import IBKRDataSource
from trading_dashboard.use_cases.lqd_hyg import register_lqd_hyg_dashboard


def test_ibkr_default_port_is_live_gateway_port() -> None:
    ds = IBKRDataSource()
    assert ds.port == 7496


def test_register_lqd_hyg_dashboard_adds_expected_widgets() -> None:
    toolkit = DashboardToolkit(data_source=IBKRDataSource())
    register_lqd_hyg_dashboard(toolkit)

    widget_ids = {widget.widget_id for widget in toolkit.layout.widgets}
    assert {
        "lqd-hyg-correlation",
        "lqd-hyg-divergence",
        "lqd-hyg-implications",
    }.issubset(widget_ids)
