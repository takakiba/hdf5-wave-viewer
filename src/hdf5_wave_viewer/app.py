from __future__ import annotations

import argparse
import sys

from PySide6 import QtCore

from .viewer import MainWindow, run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Launch the HDF5 Wave Viewer GUI")
    parser.add_argument("filename", nargs="?", help="Optional HDF5 file to open on startup")
    args = parser.parse_args(argv)

    # High-DPI displays look better with Qt's defaults in recent versions.
    rc = run_with_optional_file(args.filename)
    return int(rc)


def run_with_optional_file(filename: str | None) -> int:
    from PySide6 import QtWidgets
    import pyqtgraph as pg

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv[:1])
    pg.setConfigOptions(antialias=False)
    window = MainWindow()
    if filename:
        window.load_file(filename)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
