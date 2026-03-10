from datetime import datetime, timezone

from trading_dashboard.core.types import WidgetPayload
from trading_dashboard.ui.streamlit_app import run_streamlit_dashboard
from trading_dashboard.ui.workspace import WorkspaceManager

state = {
    "lqd-hyg-correlation": WidgetPayload(
        widget_id="lqd-hyg-correlation",
        title="LQD vs HYG Correlation",
        payload={"symbol": "LQD-HYG", "value": 0.63, "confidence": 0.63, "regime": "decoupling", "view": "metric"},
        updated_at=datetime.now(timezone.utc),
    ),
    "lqd-hyg-divergence": WidgetPayload(
        widget_id="lqd-hyg-divergence",
        title="LQD/HYG Divergence (Z)",
        payload={
            "series": [{"x": i, "y": (i - 20) / 20, "symbol": "HYG/LQD"} for i in range(1, 41)],
            "view": "timeseries",
        },
        updated_at=datetime.now(timezone.utc),
    ),
    "lqd-hyg-implications": WidgetPayload(
        widget_id="lqd-hyg-implications",
        title="Market Implications",
        payload={
            "rows": [
                {"signal": "Rolling Corr", "value": 0.63, "interpretation": "Cross-credit decoupling"},
                {"signal": "Divergence Z", "value": -1.8, "interpretation": "HYG underperforming → vol risk"},
            ],
            "view": "table",
        },
        updated_at=datetime.now(timezone.utc),
    ),
}

workspace = WorkspaceManager()
workspace.add_window("lqd-hyg-correlation", "LQD vs HYG Correlation", "metric")
workspace.add_window("lqd-hyg-divergence", "LQD/HYG Divergence (Z)", "timeseries")
workspace.add_window("lqd-hyg-implications", "Market Implications", "table")

run_streamlit_dashboard(state, workspace=workspace)
