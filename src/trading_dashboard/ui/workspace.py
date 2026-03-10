from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WindowSpec:
    widget_id: str
    title: str
    view: str
    visible: bool = True
    detached: bool = False
    x: int = 0
    y: int = 0
    w: int = 420
    h: int = 280


class WorkspaceManager:
    """Keeps window placement and detached/visible state independent from renderer."""

    def __init__(self) -> None:
        self._windows: dict[str, WindowSpec] = {}

    def add_window(self, widget_id: str, title: str, view: str, w: int = 420, h: int = 280) -> None:
        if widget_id not in self._windows:
            self._windows[widget_id] = WindowSpec(widget_id=widget_id, title=title, view=view, w=w, h=h)

    def detach(self, widget_id: str) -> None:
        self._windows[widget_id].detached = True

    def attach(self, widget_id: str) -> None:
        self._windows[widget_id].detached = False

    def show(self, widget_id: str) -> None:
        self._windows[widget_id].visible = True

    def hide(self, widget_id: str) -> None:
        self._windows[widget_id].visible = False

    def move(self, widget_id: str, x: int, y: int, w: int | None = None, h: int | None = None) -> None:
        item = self._windows[widget_id]
        item.x = x
        item.y = y
        if w is not None:
            item.w = w
        if h is not None:
            item.h = h

    def snapshot(self) -> dict[str, WindowSpec]:
        return {k: v for k, v in self._windows.items()}
