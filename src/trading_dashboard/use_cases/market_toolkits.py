from __future__ import annotations

from dataclasses import dataclass

from trading_dashboard.core.frame import LogicSnapshot
from trading_dashboard.use_cases.base import AnalysisSpec, WidgetSpec


def spy_qqq_relative_strength(snapshot: LogicSnapshot, window: int = 40) -> dict | None:
    spy = snapshot.closes("SPY", window)
    qqq = snapshot.closes("QQQ", window)
    if len(spy) < 10 or len(qqq) < 10:
        return None
    rel = [q / s for q, s in zip(qqq[-len(spy):], spy[-len(qqq):]) if s]
    if not rel:
        return None
    latest = rel[-1]
    base = rel[0]
    momentum = latest - base
    return {
        "value": momentum,
        "payload": {
            "symbol": "QQQ/SPY",
            "value": momentum,
            "ratio": latest,
            "series": [{"x": i, "y": r, "symbol": "QQQ/SPY"} for i, r in enumerate(rel[-60:], 1)],
            "view": "timeseries",
        },
    }


def rates_pressure(snapshot: LogicSnapshot, window: int = 40) -> dict | None:
    tlt = snapshot.closes("TLT", window)
    hyg = snapshot.closes("HYG", window)
    if len(tlt) < 10 or len(hyg) < 10:
        return None
    corr = snapshot.correlation("TLT", "HYG", window=min(len(tlt), len(hyg), window))
    row = [{"factor": "TLT-HYG Corr", "value": round(corr, 3), "state": "tight" if corr > 0.6 else "fragile"}]
    return {"value": corr, "payload": {"rows": row, "view": "table"}}


@dataclass(slots=True)
class CrossAssetRegimeModule:
    name: str = "cross-asset-regime"
    symbols: tuple[str, ...] = ("SPY", "QQQ", "TLT", "HYG")

    def analyses(self) -> list[AnalysisSpec]:
        return [
            AnalysisSpec(
                name="qqq-spy-relative-strength",
                symbols=("SPY", "QQQ"),
                compute=spy_qqq_relative_strength,
                widget=WidgetSpec(title="QQQ/SPY Relative Strength", view="timeseries", width=700, height=320),
            ),
            AnalysisSpec(
                name="rates-pressure",
                symbols=("TLT", "HYG"),
                compute=rates_pressure,
                widget=WidgetSpec(title="Rates vs Credit Pressure", view="table", width=620, height=280),
            ),
        ]
