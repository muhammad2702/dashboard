from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class MarketTick:
    symbol: str
    price: float
    size: float
    timestamp: datetime
    venue: str | None = None


@dataclass(slots=True)
class MarketBar:
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime


@dataclass(slots=True)
class SignalPoint:
    name: str
    symbol: str
    value: float
    confidence: float
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WidgetPayload:
    widget_id: str
    title: str
    payload: dict[str, Any]
    updated_at: datetime
