from datetime import datetime, timezone

from trading_dashboard.core.types import WidgetPayload
from trading_dashboard.ui.streamlit_app import run_streamlit_dashboard
from trading_dashboard.ui.workspace import WorkspaceManager

state = {
    "spread": WidgetPayload(
        widget_id="spread",
        title="Spread",
        payload={"symbol": "AAPL-MSFT", "value": 1.23, "confidence": 0.88, "view": "metric"},
        updated_at=datetime.now(timezone.utc),
    ),
    "corr": WidgetPayload(
        widget_id="corr",
        title="Correlation Matrix",
        payload={"matrix": [[1.0, 0.72], [0.72, 1.0]], "labels": ["AAPL", "MSFT"], "view": "matrix"},
        updated_at=datetime.now(timezone.utc),
    ),
}

workspace = WorkspaceManager()
workspace.add_window("spread", "Spread", "metric")
workspace.add_window("corr", "Correlation Matrix", "matrix")

run_streamlit_dashboard(state, workspace=workspace)
