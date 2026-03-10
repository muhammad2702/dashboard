from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from trading_dashboard.core.frame import LogicSnapshot

ComputeFn = Callable[[LogicSnapshot], Any]


@dataclass(slots=True)
class WidgetSpec:
    """Minimal UI contract for modules; dashboard layer handles rendering complexity."""

    title: str
    view: str = "metric"
    width: int = 420
    height: int = 280


@dataclass(slots=True)
class AnalysisSpec:
    """Module-provided analysis definition with compute + widget declaration."""

    name: str
    symbols: tuple[str, ...]
    compute: ComputeFn
    widget: WidgetSpec
    timeframe: str = "1m"
    lookback: int = 500
    trigger: str = "bar"


class RuntimeModule(Protocol):
    name: str
    symbols: tuple[str, ...]

    def analyses(self) -> list[AnalysisSpec]:
        ...
