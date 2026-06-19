"""Load a Zeiss SEM TIFF and print its metadata as JSON.

Usage: python load_zeiss.py [path/to/zeiss.tif]
Defaults to a bundled Zeiss Supra 40 example.
"""

import sys

from parse_sem_file import detect_vendor, parse_sem_file

DEFAULT = "examples/1908248.tif"


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    if detect_vendor(path) != "zeiss":
        raise SystemExit(f"{path} is not a Zeiss SEM TIFF")
    print(parse_sem_file(path).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
