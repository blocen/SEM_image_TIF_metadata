# SEM image TIFF metadata

Pydantic models and a parser for the metadata embedded in scanning electron
microscope (SEM) TIFF files. Two vendors are supported, auto-detected from the
TIFF tags:

- **Zeiss** — structured `CZ_SEM` tag (34118). Model: `ZeissSEMMetadata` in
  [zeiss_metadata.py](zeiss_metadata.py).
- **Hitachi** — INI-style text block in the TIFF description. Models:
  `SEMMetadata` (SU-series, dotted `Condition.*` keys) in
  [hitachi_metadata.py](hitachi_metadata.py), the flexible `HitachiSEMImage` in
  [hitachi_image.py](hitachi_image.py), and `TM3000Metadata` (tabletop TM3000
  `.txt` sidecar) in [hitachi_tm3000_metadata.py](hitachi_tm3000_metadata.py).
- **Hitachi TEM** — transmission electron microscopes (HT7700 / HT7800), flat
  `key=value` block written both as a `.txt` sidecar and into the TIFF
  ImageDescription. Model: `HitachiTEMMetadata` in
  [hitachi_tem_metadata.py](hitachi_tem_metadata.py).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Examples

The `examples/` directory contains:

- `1908*.tif` — real Zeiss Supra 40 images.
- `hitachi_example_*.tif` — synthetic Hitachi TIFFs (generated, see below).
- `hitachi_tm3000_example.txt` — a Hitachi TM3000 metadata sidecar.
- `hitachi_tem_example_*.tif` / `hitachi_tem_example.txt` — synthetic Hitachi
  TEM (HT7700/HT7800) images and sidecar (generated, see below).

### Run the Zeiss + Hitachi TIFF parser

`parse_sem_file.py` auto-detects the vendor and validates against the right
model. It runs over every `examples/*.tif`:

```bash
python parse_sem_file.py
```

To generate the synthetic Hitachi TIFFs first (the real Zeiss ones ship in the
repo):

```bash
python hitachi_make_examples.py   # writes examples/hitachi_example_*.tif
```

Parse a single file in code, or just detect the vendor:

```python
from parse_sem_file import parse_sem_file, detect_vendor

meta = parse_sem_file("examples/1908248.tif")            # -> ZeissSEMMetadata
meta = parse_sem_file("examples/hitachi_example_1.tif")  # -> SEMMetadata
print(meta.model_dump_json(indent=2))

detect_vendor("examples/1908248.tif")  # -> "zeiss"
```

### Load a single file, per vendor

Two clearly-named loaders wrap the parser for one vendor each. Both default to a
bundled example and accept an optional path; they refuse a file from the other
vendor.

```bash
python load_zeiss.py                       # bundled Zeiss Supra 40 example
python load_zeiss.py examples/1908250.tif  # any Zeiss TIFF

python load_hitachi.py                              # bundled Hitachi example
python load_hitachi.py examples/hitachi_example_2.tif  # any Hitachi TIFF
```

### Run the Hitachi TM3000 sidecar parser

The TM3000 writes a flat `key=value` `.txt` file instead of TIFF tags. Parse it
with `TM3000Metadata`:

```bash
python hitachi_tm3000_metadata.py   # parses examples/hitachi_tm3000_example.txt
```

In code:

```python
from hitachi_tm3000_metadata import TM3000Metadata

meta = TM3000Metadata.from_file("examples/hitachi_tm3000_example.txt")
print(meta.data_width, meta.data_height)
```

### Run the Hitachi TEM parser

Hitachi transmission electron microscopes (HT7700 / HT7800) write a flat
`key=value` block as a `.txt` sidecar and also embed it in the TIFF
ImageDescription. `HitachiTEMMetadata` reads either source. Generate the
synthetic examples first:

```bash
python hitachi_tem_make_examples.py   # writes examples/hitachi_tem_example_*.tif + .txt
```

Then load one:

```bash
python load_hitachi_tem.py                              # bundled .tif example
python load_hitachi_tem.py examples/hitachi_tem_example_2.tif
python load_hitachi_tem.py examples/hitachi_tem_example.txt   # the .txt sidecar
```

In code:

```python
from hitachi_tem_metadata import HitachiTEMMetadata

meta = HitachiTEMMetadata.from_tiff("examples/hitachi_tem_example_1.tif")
meta = HitachiTEMMetadata.from_file("examples/hitachi_tem_example.txt")
print(meta.accelerating_voltage_kv, meta.imaging_mode, meta.image_width)
```

The TEM examples are kept out of the SEM `parse_sem_file` dispatcher and
`convert_to_png` (which auto-detect Zeiss vs. Hitachi *SEM*); convert them with
their own script:

```bash
python convert_tem_to_png.py
# examples/hitachi_tem_example_1.tif -> converted/hitachi_tem_example_1.png
```

## Convert SEM TIFFs to PNG

Converts every `examples/*.tif` to PNG in `converted/`, tagging each output
filename with the detected vendor (via `detect_vendor`):

```bash
python convert_to_png.py
# examples/1908248.tif        -> converted/zeiss_1908248.png
# examples/hitachi_example_1.tif -> converted/hitachi_example_1.png
```
