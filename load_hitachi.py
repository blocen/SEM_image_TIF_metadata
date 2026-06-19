"""Load a Hitachi SEM TIFF and print its metadata as JSON.

Usage: python load_hitachi.py [path/to/hitachi.tif]
Defaults to a bundled synthetic Hitachi example.

For the Hitachi TM3000 `.txt` sidecar format, use hitachi_tm3000_metadata.py
instead.
"""

import sys

from parse_sem_file import detect_vendor, parse_sem_file

DEFAULT = "examples/hitachi_example_1.tif"


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    if detect_vendor(path) != "hitachi":
        raise SystemExit(f"{path} is not a Hitachi SEM TIFF")
    print(parse_sem_file(path).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
