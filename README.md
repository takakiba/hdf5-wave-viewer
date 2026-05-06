# HDF5 Wave Viewer

HDF5 Wave Viewer is a lightweight desktop viewer for large 1D time-series
datasets stored in HDF5 files.

It is intended for quickly inspecting waveform-like data without loading an
entire file into memory. The UI lists 1D datasets, lets you select up to eight
series at once, and plots a chosen time range using either strided decimation or
a min/max envelope.

## Features

- Opens HDF5 files (`.h5`, `.hdf5`, `.hdf`)
- Lists 1D datasets and their shape/dtype
- Plots up to 8 selected datasets at the same time
- Supports strided preview and min/max envelope modes for large data
- Optional mouse-wheel zoom
- Frequency units: Hz, kHz, MHz, GHz
- Time units: ns, us, ms, s
- Uses a white-background PyQtGraph plot suitable for screenshots and reports

## Installation

This project requires Python 3.10 or newer.

Install from a local checkout:

```bash
pip install .
```

Or, with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

## Usage

Launch the viewer:

```bash
hdf5-wave-viewer
```

Open a file directly on startup:

```bash
hdf5-wave-viewer path/to/data.h5
```

With uv:

```bash
uv run hdf5-wave-viewer
```

## Sampling Rate

If a dataset has one of the following HDF5 attributes, the viewer uses it as the
initial sampling rate:

- `sampling_rate`
- `fs`
- `sample_rate`
- `SamplingRate`

The value is interpreted as Hz. You can also set the sampling rate manually in
the UI.

## Viewing Modes

`stride` mode reads the requested range using HDF5 slicing and plots every Nth
sample so that the number of displayed points stays manageable.

`envelope` mode reads the requested contiguous range and computes min/max bins.
This is useful for preserving spikes in dense waveform views, but it can use
more memory for very large ranges. For first inspection of huge files, start
with `stride` mode or a smaller time window.

## Development

Install dependencies:

```bash
uv sync
```

Run the application from the source tree:

```bash
uv run hdf5-wave-viewer
```

## Notes

- Only 1D datasets are supported.
- HDF5 files may contain sensitive or proprietary measurement data. The default
  `.gitignore` excludes common HDF5 file extensions so local data files are not
  accidentally committed.
