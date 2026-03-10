from __future__ import annotations

from statistics import mean

from trading_dashboard.app import DashboardToolkit
from trading_dashboard.core.frame import LogicSnapshot


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
            "series": [{"x": i, "y": r, "symbol": "HYG/LQD"} for i, r in enumerate(ratio[-40:], 1)],
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


def register_lqd_hyg_dashboard(toolkit: DashboardToolkit) -> None:
    """Register LQD/HYG analytics windows in one line each."""

    toolkit.add_logic(
        "lqd-hyg-correlation",
        ("LQD", "HYG"),
        rolling_correlation,
        title="LQD vs HYG Correlation",
        view="metric",
    )
    toolkit.add_logic(
        "lqd-hyg-divergence",
        ("LQD", "HYG"),
        divergence_score,
        title="LQD/HYG Divergence (Z)",
        view="timeseries",
    )
    toolkit.add_logic(
        "lqd-hyg-implications",
        ("LQD", "HYG"),
        market_implications,
        title="Market Implications",
        view="table",
    )
