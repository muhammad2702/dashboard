# Trading Terminal Framework (Production, IBKR Live)

This is a **production-oriented framework** for running many analytics toolkits in one Bloomberg-style terminal surface.

- Live-only runtime (IBKR default).
- Module-agnostic core service (terminal runs independent of any single example file).
- Credit Canary (LQD/HYG) is one built-in module; you can load many modules at runtime.

## Start terminal service

```bash
pip install -e .[ui,ibkr,dev]
trading-terminal
```

## Runtime configuration (env)

- `TD_IBKR_HOST` (default `127.0.0.1`)
- `TD_IBKR_PORT` (default `7496`)
- `TD_IBKR_CLIENT_ID` (default `7`)
- `TD_RENDERER` (`streamlit` or `qt`, default `streamlit`)
- `TD_TIMEFRAME` (default `1m`)
- `TD_MODULES` built-in modules (comma-separated, e.g. `credit_canary,cross_asset_regime`)
- `TD_DYNAMIC_MODULES` runtime module classes using `package.module:ClassName`

Example:

```bash
TD_MODULES=credit_canary,cross_asset_regime \
TD_DYNAMIC_MODULES=my_pkg.my_runtime_module:MyModule \
TD_TIMEFRAME=1m trading-terminal
```

## Module interface (simple)

Your module only needs to return `AnalysisSpec` with:
- `name`
- `symbols`
- `compute(snapshot)`
- `widget=WidgetSpec(title, view, width, height)`

All complexity of data stream handling, routing, signal scheduling, and dashboard rendering stays in framework layers.

## Built-in modules

- `credit_canary`: LQD/HYG correlation, divergence, implications.
- `cross_asset_regime`: QQQ/SPY relative strength, rates-vs-credit pressure.

## Notes

- No mock/synthetic market-data fallback in runtime.
- Requires IBKR API-enabled TWS/Gateway.
