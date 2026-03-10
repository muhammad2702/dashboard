from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from trading_dashboard.core.types import SignalPoint, WidgetPayload


class DashboardWidget(ABC):
    widget_id: str
    title: str
    view: str = "metric"
    width: int = 420
    height: int = 280

    @abstractmethod
    def consume_signal(self, signal: SignalPoint) -> WidgetPayload | None:
        ...


class AutoViewWidget(DashboardWidget):
    """Generic widget for one-line logic registration."""

    def __init__(
        self,
        widget_id: str,
        title: str,
        signal_name: str,
        view: str = "metric",
        width: int = 420,
        height: int = 280,
    ) -> None:
        self.widget_id = widget_id
        self.title = title
        self.signal_name = signal_name
        self.view = view
        self.width = width
        self.height = height

    def consume_signal(self, signal: SignalPoint) -> WidgetPayload | None:
        if signal.name != self.signal_name:
            return None
        payload = signal.metadata.get("payload", {"value": signal.value})
        if not isinstance(payload, dict):
            payload = {"value": payload}
        payload.setdefault("symbol", signal.symbol)
        payload.setdefault("value", signal.value)
        payload.setdefault("confidence", signal.confidence)
        payload.setdefault("view", signal.metadata.get("view", self.view))
        payload.setdefault("size", {"w": self.width, "h": self.height})
        return WidgetPayload(
            widget_id=self.widget_id,
            title=self.title,
            payload=payload,
            updated_at=signal.timestamp,
        )


class TimeSeriesWidget(DashboardWidget):
    def __init__(self, widget_id: str, title: str, signal_name: str, max_points: int = 300) -> None:
        self.widget_id = widget_id
        self.title = title
        self.signal_name = signal_name
        self.max_points = max_points
        self.view = "timeseries"
        self._series: list[dict[str, Any]] = []

    def consume_signal(self, signal: SignalPoint) -> WidgetPayload | None:
        if signal.name != self.signal_name:
            return None
        self._series.append({"x": signal.timestamp, "y": signal.value, "symbol": signal.symbol})
        self._series = self._series[-self.max_points :]
        return WidgetPayload(
            widget_id=self.widget_id,
            title=self.title,
            payload={"series": self._series, "view": self.view},
            updated_at=signal.timestamp,
        )
