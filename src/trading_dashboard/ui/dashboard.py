from __future__ import annotations

from collections import OrderedDict

from trading_dashboard.core.types import SignalPoint, WidgetPayload
from trading_dashboard.ui.widgets import DashboardWidget
from trading_dashboard.ui.workspace import WorkspaceManager


class DashboardLayout:
    """Widget registry + window/workspace model."""

    def __init__(self) -> None:
        self._widgets: OrderedDict[str, DashboardWidget] = OrderedDict()
        self._state: dict[str, WidgetPayload] = {}
        self.workspace = WorkspaceManager()

    def register_widget(self, widget: DashboardWidget) -> None:
        self._widgets[widget.widget_id] = widget
        self.workspace.add_window(widget.widget_id, widget.title, widget.view, w=widget.width, h=widget.height)

    async def on_signal(self, signal: SignalPoint) -> None:
        for widget in self._widgets.values():
            payload = widget.consume_signal(signal)
            if payload is not None:
                self._state[payload.widget_id] = payload

    @property
    def state(self) -> dict[str, WidgetPayload]:
        return dict(self._state)

    @property
    def widgets(self) -> list[DashboardWidget]:
        return list(self._widgets.values())
