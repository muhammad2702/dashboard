from __future__ import annotations

from typing import Any


def run_streamlit_dashboard(state: dict[str, Any], workspace: Any | None = None, columns: int = 4) -> None:
    import pandas as pd
    import plotly.express as px
    import streamlit as st

    st.set_page_config(page_title="Trading Terminal", layout="wide")
    st.title("Trading Signal Terminal")

    visible_ids = list(state.keys())
    if workspace is not None:
        st.sidebar.header("Workspace")
        for widget_id, win in workspace.snapshot().items():
            shown = st.sidebar.checkbox(f"{win.title}", value=win.visible, key=f"show-{widget_id}")
            if shown:
                workspace.show(widget_id)
            else:
                workspace.hide(widget_id)
            if st.sidebar.button(f"Toggle detach: {win.title}", key=f"detach-{widget_id}"):
                workspace.attach(widget_id) if win.detached else workspace.detach(widget_id)
        visible_ids = [wid for wid, win in workspace.snapshot().items() if win.visible and wid in state]

    grid = st.columns(columns)
    for idx, widget_id in enumerate(visible_ids):
        payload = state[widget_id]
        with grid[idx % columns]:
            st.subheader(payload.title)
            data = payload.payload
            view = data.get("view", "metric")
            if "series" in data or view == "timeseries":
                df = pd.DataFrame(data.get("series", []))
                if not df.empty:
                    st.plotly_chart(px.line(df, x="x", y="y", color="symbol"), use_container_width=True)
                else:
                    st.info("Waiting for series data...")
            elif view == "matrix":
                matrix = data.get("matrix", [])
                labels = data.get("labels")
                if matrix:
                    st.plotly_chart(px.imshow(matrix, x=labels, y=labels, text_auto=True), use_container_width=True)
                else:
                    st.info("Waiting for matrix data...")
            elif view == "network" or "edges" in data:
                st.json({"focus": data.get("focus"), "edges": data.get("edges", [])})
            elif view == "table":
                st.dataframe(pd.DataFrame(data.get("rows", [])), use_container_width=True)
            else:
                st.metric(label=data.get("symbol", "value"), value=round(float(data.get("value", 0.0)), 4))
                st.caption(f"confidence={data.get('confidence', 0)}")
