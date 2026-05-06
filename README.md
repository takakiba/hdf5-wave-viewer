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

Clone the repository:

```bash
git clone https://github.com/takakiba/hdf5-wave-viewer.git
cd hdf5-wave-viewer
```

Install from the cloned checkout:

```bash
pip install .
```

Or, with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

## Usage

After installation, launch the viewer:

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

## 日本語での使い方

Python 3.10 以上が必要です。

まず、リポジトリを clone します。

```bash
git clone https://github.com/takakiba/hdf5-wave-viewer.git
cd hdf5-wave-viewer
```

通常の Python 環境でインストールする場合:

```bash
pip install .
```

viewer を起動します。

```bash
hdf5-wave-viewer
```

起動時に HDF5 ファイルを指定することもできます。

```bash
hdf5-wave-viewer path/to/data.h5
```

`uv` を使う場合:

```bash
uv sync
uv run hdf5-wave-viewer
```

画面上で HDF5 ファイルを開くと、1次元 dataset の一覧が表示されます。
表示したい dataset を選択し、sampling rate、表示する時間範囲、表示モードを
指定して `Reload view` を押すと波形が描画されます。

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

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
