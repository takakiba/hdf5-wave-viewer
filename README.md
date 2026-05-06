# HDF5 Wave Viewer

Minimal HDF5 time-series viewer for large 1D datasets.

Install locally:

```bash
pip install .
hdf5-wave-viewer
```

With uv:

```bash
uv sync
uv run hdf5-wave-viewer
```

Features:

- white background plotting
- up to 8 simultaneously selected 1D datasets
- stride and min/max-envelope modes
- optional wheel zoom
- frequency units: Hz, kHz, MHz, GHz
- time units: ns, us, ms, s
