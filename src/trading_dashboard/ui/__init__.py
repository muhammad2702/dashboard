"""UI layouts and renderers."""

from trading_dashboard.ui.dashboard import DashboardLayout
from trading_dashboard.ui.widgets import AutoViewWidget, DashboardWidget, TimeSeriesWidget
from trading_dashboard.ui.workspace import WindowSpec, WorkspaceManager

__all__ = [
    "AutoViewWidget",
    "DashboardLayout",
    "DashboardWidget",
    "TimeSeriesWidget",
    "WindowSpec",
    "WorkspaceManager",
]
