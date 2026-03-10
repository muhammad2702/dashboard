from __future__ import annotations

from typing import Any


def run_qt_terminal(layout: Any) -> None:
    """Optional desktop renderer with detachable dock widgets.

    Requires: pip install .[desktop]
    """

    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QDockWidget, QWidget, QVBoxLayout
    except ImportError as exc:  # pragma: no cover - optional runtime
        raise RuntimeError("PySide6 is required for the detachable desktop terminal. Install with: pip install .[desktop]") from exc

    app = QApplication.instance() or QApplication([])
    main = QMainWindow()
    main.setWindowTitle("Trading Terminal Workspace")

    for widget in layout.widgets:
        dock = QDockWidget(widget.title)
        dock.setObjectName(widget.widget_id)
        dock.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            | QDockWidget.DockWidgetClosable
        )
        container = QWidget()
        vbox = QVBoxLayout()
        payload = layout.state.get(widget.widget_id)
        text = QLabel(str(payload.payload if payload else "Waiting for data..."))
        text.setWordWrap(True)
        vbox.addWidget(text)
        container.setLayout(vbox)
        dock.setWidget(container)
        main.addDockWidget(Qt.LeftDockWidgetArea, dock)

    main.resize(1600, 900)
    main.show()
    app.exec()
