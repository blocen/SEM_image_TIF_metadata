"""Load Hitachi TEM (HT7700 / HT7800) metadata and print it as JSON.

Usage:
  python load_hitachi_tem.py                          # bundled .tif example
  python load_hitachi_tem.py examples/foo.tif         # any TEM TIFF
  python load_hitachi_tem.py examples/foo.txt         # any TEM .txt sidecar

Reads the embedded ImageDescription block for .tif/.tiff, or the flat
key=value block for a .txt sidecar.
"""

import sys

from hitachi_tem_metadata import HitachiTEMMetadata

DEFAULT = "examples/hitachi_tem_example_1.tif"


def load(path: str) -> HitachiTEMMetadata:
    if path.lower().endswith((".tif", ".tiff")):
        return HitachiTEMMetadata.from_tiff(path)
    return HitachiTEMMetadata.from_file(path)


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    meta = load(path)
    print(meta.model_dump_json(indent=2))
    print(f"\n{meta.image_width} x {meta.image_height} px")


if __name__ == "__main__":
    main()
