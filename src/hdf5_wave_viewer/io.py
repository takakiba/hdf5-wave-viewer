from __future__ import annotations

from dataclasses import dataclass

import h5py


@dataclass(frozen=True)
class DatasetInfo:
    path: str
    shape: tuple[int, ...]
    dtype: str
    sampling_rate: float | None = None


def list_1d_datasets(filename: str) -> list[DatasetInfo]:
    """Return all 1D datasets in an HDF5 file."""

    results: list[DatasetInfo] = []

    def visitor(name: str, obj):
        if isinstance(obj, h5py.Dataset) and obj.ndim == 1:
            fs = None
            for key in ("sampling_rate", "fs", "sample_rate", "SamplingRate"):
                if key in obj.attrs:
                    try:
                        fs = float(obj.attrs[key])
                    except Exception:
                        fs = None
                    break
            results.append(
                DatasetInfo(
                    path="/" + name,
                    shape=tuple(obj.shape),
                    dtype=str(obj.dtype),
                    sampling_rate=fs,
                )
            )

    with h5py.File(filename, "r") as f:
        f.visititems(visitor)

    return sorted(results, key=lambda item: item.path)


def get_dataset_length(filename: str, dataset_path: str) -> int:
    with h5py.File(filename, "r") as f:
        if dataset_path not in f:
            raise KeyError(f"Dataset not found: {dataset_path}")
        dset = f[dataset_path]
        if dset.ndim != 1:
            raise ValueError(f"Only 1D datasets are supported. Got shape={dset.shape}")
        return int(dset.shape[0])
