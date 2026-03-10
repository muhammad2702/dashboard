from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from trading_dashboard.core.frame import LogicSnapshot
from trading_dashboard.use_cases.base import AnalysisSpec, WidgetSpec


def _zscore(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = mean(values)
    var = sum((v - mu) ** 2 for v in values) / (len(values) - 1)
    std = var**0.5
    if std == 0:
        return 0.0
    return (values[-1] - mu) / std


def rolling_correlation(snapshot: LogicSnapshot, window: int = 60) -> dict:
    corr = snapshot.correlation("LQD", "HYG", window=window)
    regime = "coupled" if corr >= 0.8 else "decoupling" if corr >= 0.5 else "stress"
    return {
        "value": corr,
        "confidence": min(abs(corr), 1.0),
        "payload": {
            "symbol": "LQD-HYG",
            "value": corr,
            "regime": regime,
            "view": "metric",
        },
    }


def divergence_score(snapshot: LogicSnapshot, window: int = 80) -> dict | None:
    lqd = snapshot.closes("LQD", window)
    hyg = snapshot.closes("HYG", window)
    n = min(len(lqd), len(hyg))
    if n < 20:
        return None
    ratio = [h / l for h, l in zip(hyg[-n:], lqd[-n:]) if l]
    if len(ratio) < 20:
        return None

    z = _zscore(ratio)
    latest = ratio[-1]
    implication = "risk-on" if z > 1.5 else "risk-off-warning" if z < -1.5 else "neutral"

    return {
        "value": z,
        "payload": {
            "symbol": "HYG/LQD",
            "value": z,
            "ratio": latest,
            "implication": implication,
            "series": [{"x": i, "y": r, "symbol": "HYG/LQD"} for i, r in enumerate(ratio[-60:], 1)],
            "view": "timeseries",
        },
    }


def market_implications(snapshot: LogicSnapshot) -> dict | None:
    corr_payload = rolling_correlation(snapshot)
    div_payload = divergence_score(snapshot)
    if div_payload is None:
        return None

    corr = float(corr_payload["value"])
    z = float(div_payload["value"])
    rows = [
        {
            "signal": "Rolling Corr",
            "value": round(corr, 3),
            "interpretation": "Risk transmission strong" if corr >= 0.8 else "Cross-credit decoupling",
        },
        {
            "signal": "Divergence Z",
            "value": round(z, 3),
            "interpretation": "HYG underperforming → vol risk" if z < -1.5 else "No extreme divergence",
        },
    ]

    return {
        "value": z,
        "payload": {
            "rows": rows,
            "view": "table",
        },
    }


@dataclass(slots=True)
class CreditCanaryModule:
    name: str = "credit-canary"
    symbols: tuple[str, ...] = ("LQD", "HYG")

    def analyses(self) -> list[AnalysisSpec]:
        return [
            AnalysisSpec(
                name="lqd-hyg-correlation",
                symbols=("LQD", "HYG"),
                compute=rolling_correlation,
                widget=WidgetSpec(title="LQD vs HYG Correlation", view="metric", width=420, height=220),
            ),
            AnalysisSpec(
                name="lqd-hyg-divergence",
                symbols=("LQD", "HYG"),
                compute=divergence_score,
                widget=WidgetSpec(title="LQD/HYG Divergence (Z)", view="timeseries", width=700, height=320),
            ),
            AnalysisSpec(
                name="lqd-hyg-implications",
                symbols=("LQD", "HYG"),
                compute=market_implications,
                widget=WidgetSpec(title="Market Implications", view="table", width=620, height=280),
            ),
        ]


def register_lqd_hyg_dashboard(toolkit) -> None:
    toolkit.install_module(CreditCanaryModule())
