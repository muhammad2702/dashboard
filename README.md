# LQD vs HYG IBKR Terminal

This project is now focused on a single production use case:
**LQD vs HYG credit-regime monitoring** with IBKR live data.

## What it does

- Connects to **IBKR TWS/Gateway on port `7496`** by default.
- Streams LQD and HYG bars/ticks.
- Computes ready-to-use windows:
  - Rolling correlation regime (`coupled` / `decoupling` / `stress`)
  - HYG/LQD divergence z-score (risk-on vs risk-off warning)
  - Market implications table for quick interpretation
- Supports detachable workspace state and optional desktop dock windows.

## Quick start

```bash
pip install -e .[ui,ibkr,dev]
python examples/demo.py
```

This starts the live Streamlit terminal and subscribes to `LQD` and `HYG` using IBKR (no synthetic feed fallback).

## One-line logic registration

You can still add custom logic with one line:

```python
toolkit.add_logic("my-metric", ("LQD", "HYG"), my_compute_fn, view="metric")
```

The framework handles data routing, execution, and widget wiring.

## LQD/HYG packaged use-case

`register_lqd_hyg_dashboard(toolkit)` registers three default windows:

1. `lqd-hyg-correlation`
2. `lqd-hyg-divergence`
3. `lqd-hyg-implications`

Source: `src/trading_dashboard/use_cases/lqd_hyg.py`.

## Notes

- IBKR must be running and API-enabled.
- Default connection is `127.0.0.1:7496`.
- This repository intentionally avoids synthetic/mock market feeds in runtime examples.
- Optional desktop detachable renderer:

```bash
pip install -e .[desktop]
```
