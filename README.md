# Trading Dashboard Framework (detachable terminal workspace)

A Python framework for building a Bloomberg-style trading terminal where you:

1. write **only your signal logic**,
2. register it in **one line**,
3. get automatic data subscriptions + plotting widgets,
4. place widgets as **detachable windows** in a shared workspace.

## What changed vs. simple static dashboards

- **Detachable window model**: each panel has visibility/detach/position state in `WorkspaceManager`.
- **One-line signal registration**: `toolkit.add_logic(...)` wires subscriptions, signal execution, and UI widget.
- **Multi-symbol logic-first API**: your function receives a rolling snapshot and can compute pair-spread, correlation matrix, network data, etc.
- **Renderer-agnostic architecture**:
  - `Streamlit` renderer (web, fast iteration, show/hide + detach flags)
  - `Qt` renderer (desktop, true floating dock widgets)

## Architecture

```text
IBKRDataSource (default) / other adapters
        │
        ▼
DataRouter (async fan-out)
        │
        ▼
SignalEngine
  + ExpressionIndicator (logic fn over rolling snapshot)
        │
        ▼
DashboardLayout
  + WorkspaceManager (detached/visible/position state)
        │
        ▼
Renderer
  - Streamlit terminal
  - Qt dockable terminal (detachable windows)
```

## Your workflow (the important part)

```python
from trading_dashboard import DashboardToolkit

# write your logic function only

def pair_corr(snapshot):
    corr = snapshot.correlation("AAPL", "MSFT", window=40)
    return {
        "value": corr,
        "payload": {
            "matrix": [[1.0, corr], [corr, 1.0]],
            "labels": ["AAPL", "MSFT"],
            "view": "matrix",
        },
    }

# one line to register everything
# (data pull + execution + render block)
toolkit.add_logic("pair-corr", ("AAPL", "MSFT"), pair_corr, view="matrix")
```

No manual routing, no manual UI update loop per indicator, no per-indicator data adapters.

## Key files

- `src/trading_dashboard/app.py` – `DashboardToolkit` + `add_logic(...)`
- `src/trading_dashboard/core/frame.py` – rolling snapshot helpers (`correlation`, `latest_bar`, etc.)
- `src/trading_dashboard/signals/dsl.py` – `ExpressionIndicator`
- `src/trading_dashboard/ui/workspace.py` – detachable/visible window state
- `src/trading_dashboard/ui/qt_terminal.py` – desktop detachable dock windows
- `src/trading_dashboard/ui/streamlit_app.py` – web renderer

## Install

```bash
pip install -e .[dev]
pip install -e .[ui]       # streamlit renderer
pip install -e .[desktop]  # detachable Qt desktop renderer
pip install -e .[ibkr]     # IBKR integration
```

## Run demo

```bash
python examples/demo.py
```

(Uses mock data by default. Swap to `IBKRDataSource` for live market data.)
