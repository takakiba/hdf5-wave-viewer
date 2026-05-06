from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import h5py

Mode = Literal["stride", "envelope"]


@dataclass(frozen=True)
class ViewData:
    """Data prepared for plotting."""

    t: np.ndarray
    y: np.ndarray
    y_min: np.ndarray | None = None
    y_max: np.ndarray | None = None
    mode: Mode = "stride"


def time_to_index(t: float, fs: float) -> int:
    return int(round(float(t) * float(fs)))


def _clip_range(i0: int, i1: int, n_total: int) -> tuple[int, int]:
    if n_total <= 0:
        raise ValueError("Dataset is empty")
    i0 = max(0, min(int(i0), n_total - 1))
    i1 = max(i0 + 1, min(int(i1), n_total))
    return i0, i1


def read_stride(
    dset: h5py.Dataset,
    fs: float,
    t0: float,
    t1: float,
    target_points: int = 50_000,
) -> ViewData:
    """Read a decimated time range using HDF5 slicing."""

    if dset.ndim != 1:
        raise ValueError(f"Only 1D datasets are supported. Got shape={dset.shape}")
    if t1 <= t0:
        raise ValueError("t1 must be larger than t0")
    if fs <= 0:
        raise ValueError("fs must be positive")
    if target_points <= 0:
        raise ValueError("target_points must be positive")

    i0 = time_to_index(t0, fs)
    i1 = time_to_index(t1, fs)
    i0, i1 = _clip_range(i0, i1, dset.shape[0])

    nsel = i1 - i0
    stride = max(1, int(np.ceil(nsel / target_points)))

    y = np.asarray(dset[i0:i1:stride])
    indices = i0 + np.arange(len(y), dtype=np.float64) * stride
    t = indices / fs

    return ViewData(t=t, y=y, mode="stride")


def read_envelope(
    dset: h5py.Dataset,
    fs: float,
    t0: float,
    t1: float,
    target_bins: int = 5_000,
) -> ViewData:
    """Read a time range and compute min/max envelope bins.

    This implementation intentionally avoids loading the whole file, but it does
    read one contiguous time range into memory. It is intended for interactive
    views after restricting t0/t1. For very large full-range views, reduce
    target_bins or use stride mode first.
    """

    if dset.ndim != 1:
        raise ValueError(f"Only 1D datasets are supported. Got shape={dset.shape}")
    if t1 <= t0:
        raise ValueError("t1 must be larger than t0")
    if fs <= 0:
        raise ValueError("fs must be positive")
    if target_bins <= 0:
        raise ValueError("target_bins must be positive")

    i0 = time_to_index(t0, fs)
    i1 = time_to_index(t1, fs)
    i0, i1 = _clip_range(i0, i1, dset.shape[0])

    nsel = i1 - i0
    nbins = min(int(target_bins), nsel)
    bin_size = max(1, nsel // nbins)
    n_use = bin_size * nbins

    # Read only the used contiguous range, then aggregate in NumPy.
    y_raw = np.asarray(dset[i0 : i0 + n_use])
    yy = y_raw.reshape(nbins, bin_size)

    y_min = np.nanmin(yy, axis=1)
    y_max = np.nanmax(yy, axis=1)
    y_mid = 0.5 * (y_min + y_max)

    centers = i0 + (np.arange(nbins, dtype=np.float64) + 0.5) * bin_size
    t = centers / fs

    return ViewData(t=t, y=y_mid, y_min=y_min, y_max=y_max, mode="envelope")


def read_view(
    filename: str,
    dataset_path: str,
    fs: float,
    t0: float,
    t1: float,
    target_points: int,
    mode: Mode,
) -> ViewData:
    with h5py.File(filename, "r") as f:
        if dataset_path not in f:
            raise KeyError(f"Dataset not found: {dataset_path}")
        dset = f[dataset_path]
        if mode == "stride":
            return read_stride(dset, fs, t0, t1, target_points)
        if mode == "envelope":
            return read_envelope(dset, fs, t0, t1, target_points)
        raise ValueError(f"Unknown mode: {mode}")
