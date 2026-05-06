from __future__ import annotations

import traceback

import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets

from .downsample import read_view
from .io import DatasetInfo, get_dataset_length, list_1d_datasets


MAX_SELECTED_DATASETS = 8

FREQUENCY_UNITS = {
    "Hz": 1.0,
    "kHz": 1.0e3,
    "MHz": 1.0e6,
    "GHz": 1.0e9,
}

TIME_UNITS = {
    "ns": 1.0e-9,
    "us": 1.0e-6,
    "ms": 1.0e-3,
    "s": 1.0,
}


class WheelControlledViewBox(pg.ViewBox):
    """ViewBox with optional mouse-wheel zoom.

    PyQtGraph zooms with the mouse wheel by default. For large time-series
    inspection, accidental wheel zoom can make the current range easy to lose,
    so this viewer disables wheel zoom unless the user explicitly enables it.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wheel_zoom_enabled = False

    def set_wheel_zoom_enabled(self, enabled: bool) -> None:
        self.wheel_zoom_enabled = bool(enabled)

    def wheelEvent(self, ev, axis=None):  # noqa: N802 - Qt/pyqtgraph API name
        if self.wheel_zoom_enabled:
            super().wheelEvent(ev, axis=axis)
        else:
            ev.ignore()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("HDF5 Wave Viewer")
        self.resize(1200, 760)

        self.filename: str | None = None
        self.datasets: list[DatasetInfo] = []
        self._path_to_info: dict[str, DatasetInfo] = {}

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        controls = QtWidgets.QGridLayout()
        layout.addLayout(controls)

        self.file_edit = QtWidgets.QLineEdit()
        self.file_button = QtWidgets.QPushButton("Open HDF5...")

        self.dataset_list = QtWidgets.QListWidget()
        self.dataset_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.dataset_list.setMaximumHeight(150)
        self.dataset_list.setAlternatingRowColors(True)

        self.fs_spin = QtWidgets.QDoubleSpinBox()
        self.fs_spin.setDecimals(9)
        self.fs_spin.setRange(1.0e-12, 1.0e15)
        self.fs_unit_combo = QtWidgets.QComboBox()
        self.fs_unit_combo.addItems(list(FREQUENCY_UNITS.keys()))
        self.fs_unit_combo.setCurrentText("MHz")
        self.fs_spin.setValue(100.0)

        self.t0_spin = QtWidgets.QDoubleSpinBox()
        self.t0_spin.setDecimals(9)
        self.t0_spin.setRange(0.0, 1e18)
        self.t0_spin.setValue(0.0)

        self.t1_spin = QtWidgets.QDoubleSpinBox()
        self.t1_spin.setDecimals(9)
        self.t1_spin.setRange(0.0, 1e18)
        self.t1_spin.setValue(1.0)
        self.time_unit_combo = QtWidgets.QComboBox()
        self.time_unit_combo.addItems(list(TIME_UNITS.keys()))
        self.time_unit_combo.setCurrentText("s")
        self._last_frequency_factor = FREQUENCY_UNITS[self.fs_unit_combo.currentText()]
        self._last_time_factor = TIME_UNITS[self.time_unit_combo.currentText()]

        self.target_spin = QtWidgets.QSpinBox()
        self.target_spin.setRange(100, 10_000_000)
        self.target_spin.setValue(50_000)

        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(["stride", "envelope"])

        self.reload_button = QtWidgets.QPushButton("Reload view")
        self.full_button = QtWidgets.QPushButton("Set full range")
        self.clear_selection_button = QtWidgets.QPushButton("Clear selection")
        self.wheel_zoom_checkbox = QtWidgets.QCheckBox("Enable wheel zoom")
        self.wheel_zoom_checkbox.setChecked(False)

        controls.addWidget(QtWidgets.QLabel("File"), 0, 0)
        controls.addWidget(self.file_edit, 0, 1, 1, 5)
        controls.addWidget(self.file_button, 0, 6)

        controls.addWidget(QtWidgets.QLabel("Datasets (select up to 8)"), 1, 0)
        controls.addWidget(self.dataset_list, 1, 1, 1, 6)

        controls.addWidget(QtWidgets.QLabel("fs"), 2, 0)
        controls.addWidget(self.fs_spin, 2, 1)
        controls.addWidget(self.fs_unit_combo, 2, 2)
        controls.addWidget(QtWidgets.QLabel("t0"), 2, 3)
        controls.addWidget(self.t0_spin, 2, 4)
        controls.addWidget(QtWidgets.QLabel("t1"), 2, 5)
        controls.addWidget(self.t1_spin, 2, 6)
        controls.addWidget(self.time_unit_combo, 2, 7)

        controls.addWidget(QtWidgets.QLabel("Target points/bins"), 3, 0)
        controls.addWidget(self.target_spin, 3, 1)
        controls.addWidget(QtWidgets.QLabel("Mode"), 3, 2)
        controls.addWidget(self.mode_combo, 3, 3)
        controls.addWidget(self.reload_button, 3, 4)
        controls.addWidget(self.full_button, 3, 5)
        controls.addWidget(self.clear_selection_button, 3, 6)
        controls.addWidget(self.wheel_zoom_checkbox, 3, 7)

        self.view_box = WheelControlledViewBox()
        self.plot = pg.PlotWidget(background="w", viewBox=self.view_box)
        self.plot.setLabel("bottom", "Time", units="s")
        self.plot.setLabel("left", "Signal")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.addLegend(offset=(10, 10))
        self._set_plot_white_theme()
        layout.addWidget(self.plot, stretch=1)

        self.status = QtWidgets.QLabel("Open an HDF5 file to begin.")
        layout.addWidget(self.status)

        self.file_button.clicked.connect(self.open_file_dialog)
        self.reload_button.clicked.connect(self.reload_view)
        self.full_button.clicked.connect(self.set_full_range)
        self.clear_selection_button.clicked.connect(self.dataset_list.clearSelection)
        self.dataset_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.wheel_zoom_checkbox.toggled.connect(self.view_box.set_wheel_zoom_enabled)
        self.fs_unit_combo.currentTextChanged.connect(self.on_frequency_unit_changed)
        self.time_unit_combo.currentTextChanged.connect(self.on_time_unit_changed)


    def frequency_unit_factor(self) -> float:
        return FREQUENCY_UNITS[self.fs_unit_combo.currentText()]

    def time_unit_factor(self) -> float:
        return TIME_UNITS[self.time_unit_combo.currentText()]

    def fs_hz(self) -> float:
        return self.fs_spin.value() * self.frequency_unit_factor()

    def t0_seconds(self) -> float:
        return self.t0_spin.value() * self.time_unit_factor()

    def t1_seconds(self) -> float:
        return self.t1_spin.value() * self.time_unit_factor()

    def set_fs_hz(self, fs_hz: float) -> None:
        self.fs_spin.setValue(float(fs_hz) / self.frequency_unit_factor())

    def set_time_range_seconds(self, t0: float, t1: float) -> None:
        factor = self.time_unit_factor()
        self.t0_spin.setValue(float(t0) / factor)
        self.t1_spin.setValue(float(t1) / factor)

    def on_frequency_unit_changed(self, new_unit: str) -> None:
        old_factor = getattr(self, "_last_frequency_factor", FREQUENCY_UNITS["MHz"])
        fs_hz = self.fs_spin.value() * old_factor
        self.fs_spin.setValue(fs_hz / FREQUENCY_UNITS[new_unit])
        self._last_frequency_factor = FREQUENCY_UNITS[new_unit]

    def on_time_unit_changed(self, new_unit: str) -> None:
        old_factor = getattr(self, "_last_time_factor", TIME_UNITS["s"])
        t0 = self.t0_spin.value() * old_factor
        t1 = self.t1_spin.value() * old_factor
        new_factor = TIME_UNITS[new_unit]
        self.t0_spin.setValue(t0 / new_factor)
        self.t1_spin.setValue(t1 / new_factor)
        self._last_time_factor = new_factor
        self.plot.setLabel("bottom", "Time", units=new_unit)

    def _set_plot_white_theme(self) -> None:
        self.plot.setBackground("w")
        plot_item = self.plot.getPlotItem()
        for axis_name in ("left", "bottom", "right", "top"):
            axis = plot_item.getAxis(axis_name)
            axis.setPen(pg.mkPen("k"))
            axis.setTextPen(pg.mkPen("k"))
        plot_item.getViewBox().setBackgroundColor("w")

    def open_file_dialog(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open HDF5 file",
            "",
            "HDF5 files (*.h5 *.hdf5 *.hdf);;All files (*)",
        )
        if path:
            self.load_file(path)

    def load_file(self, path: str) -> None:
        try:
            self.filename = path
            self.file_edit.setText(path)
            self.datasets = list_1d_datasets(path)
            self._path_to_info = {info.path: info for info in self.datasets}
            self.dataset_list.clear()
            for info in self.datasets:
                label = f"{info.path}  shape={info.shape} dtype={info.dtype}"
                item = QtWidgets.QListWidgetItem(label)
                item.setData(QtCore.Qt.UserRole, info.path)
                self.dataset_list.addItem(item)
            self.status.setText(f"Found {len(self.datasets)} 1D dataset(s). Select up to {MAX_SELECTED_DATASETS}.")
            if self.datasets:
                self.dataset_list.item(0).setSelected(True)
                self.on_selection_changed()
        except Exception as exc:
            self.show_error("Failed to open HDF5 file", exc)

    def selected_dataset_paths(self) -> list[str]:
        items = self.dataset_list.selectedItems()
        return [item.data(QtCore.Qt.UserRole) for item in items]

    def on_selection_changed(self) -> None:
        paths = self.selected_dataset_paths()
        if not paths:
            return
        first = self._path_to_info.get(paths[0])
        if first and first.sampling_rate is not None:
            self.set_fs_hz(first.sampling_rate)
        if len(paths) > MAX_SELECTED_DATASETS:
            self.status.setText(
                f"{len(paths)} datasets selected; only the first {MAX_SELECTED_DATASETS} will be plotted."
            )
        else:
            self.status.setText(f"{len(paths)} dataset(s) selected.")

    def set_full_range(self) -> None:
        if not self.filename:
            return
        paths = self.selected_dataset_paths()
        if not paths:
            return
        fs = self.fs_hz()
        lengths = [get_dataset_length(self.filename, path) for path in paths[:MAX_SELECTED_DATASETS]]
        n = min(lengths)
        t1_s = n / fs
        self.set_time_range_seconds(0.0, t1_s)
        t_unit = self.time_unit_combo.currentText()
        t1_display = t1_s / self.time_unit_factor()
        if len(lengths) == 1:
            self.status.setText(f"Full range set: 0 to {t1_display:.9g} {t_unit} ({n} samples).")
        else:
            self.status.setText(
                f"Common full range set: 0 to {t1_display:.9g} {t_unit} "
                f"(minimum length among selected datasets: {n} samples)."
            )

    def _series_pen(self, index: int, width: float = 1.4, alpha: int = 255, style=None):
        color = pg.intColor(index, hues=MAX_SELECTED_DATASETS, values=1, maxValue=255)
        color.setAlpha(alpha)
        kwargs = {"color": color, "width": width}
        if style is not None:
            kwargs["style"] = style
        return pg.mkPen(**kwargs)

    def reload_view(self) -> None:
        if not self.filename:
            self.status.setText("No HDF5 file selected.")
            return
        paths = self.selected_dataset_paths()
        if not paths:
            self.status.setText("No 1D dataset selected.")
            return

        paths = paths[:MAX_SELECTED_DATASETS]
        mode = self.mode_combo.currentText()
        time_unit = self.time_unit_combo.currentText()
        time_factor = self.time_unit_factor()

        try:
            self.plot.setLabel("bottom", "Time", units=time_unit)
            self.plot.clear()
            self.plot.addLegend(offset=(10, 10))

            plotted = 0
            total_points = 0
            for idx, dspath in enumerate(paths):
                data = read_view(
                    filename=self.filename,
                    dataset_path=dspath,
                    fs=self.fs_hz(),
                    t0=self.t0_seconds(),
                    t1=self.t1_seconds(),
                    target_points=self.target_spin.value(),
                    mode=mode,
                )

                name = dspath.rsplit("/", 1)[-1] or dspath
                if len(paths) > 1:
                    parent = dspath.rsplit("/", 1)[0]
                    name = f"{parent}/{name}" if parent else name

                xdata = data.t / time_factor
                main_pen = self._series_pen(idx, width=1.5)
                faint_pen = self._series_pen(idx, width=0.9, alpha=140, style=QtCore.Qt.DotLine)

                if data.mode == "envelope" and data.y_min is not None and data.y_max is not None:
                    self.plot.plot(xdata, data.y_min, pen=faint_pen, name=f"{name} min")
                    self.plot.plot(xdata, data.y_max, pen=faint_pen, name=f"{name} max")
                    self.plot.plot(xdata, data.y, pen=main_pen, name=f"{name} mid")
                else:
                    self.plot.plot(xdata, data.y, pen=main_pen, name=name)

                plotted += 1
                total_points += len(data.t)

            if mode == "envelope":
                self.status.setText(
                    f"Envelope view: {plotted} dataset(s), {total_points} total bins plotted."
                )
            else:
                self.status.setText(
                    f"Stride view: {plotted} dataset(s), {total_points} total points plotted."
                )

        except Exception as exc:
            self.show_error("Failed to reload view", exc)

    def show_error(self, title: str, exc: Exception) -> None:
        detail = traceback.format_exc()
        self.status.setText(f"{title}: {exc}")
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Critical)
        box.setWindowTitle(title)
        box.setText(str(exc))
        box.setDetailedText(detail)
        box.exec()


def run() -> int:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    pg.setConfigOptions(antialias=False, background="w", foreground="k")
    window = MainWindow()
    window.show()
    return app.exec()
