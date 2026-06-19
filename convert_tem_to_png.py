"""Convert the Hitachi TEM example TIFFs to PNG in converted/, prefixing each
output filename with hitachi_tem_."""

from pathlib import Path

from PIL import Image

SRC_DIR = Path("examples")
OUT_DIR = Path("converted")
PREFIX = "hitachi_tem_example"


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    tifs = sorted(
        p
        for p in SRC_DIR.iterdir()
        if p.suffix.lower() in {".tif", ".tiff"} and p.stem.startswith(PREFIX)
    )
    if not tifs:
        raise SystemExit(
            "No TEM examples found. Run: python hitachi_tem_make_examples.py"
        )
    for tif in tifs:
        out = OUT_DIR / f"{tif.stem}.png"
        with Image.open(tif) as img:
            img.save(out)
        print(f"converted {tif} -> {out}")


if __name__ == "__main__":
    main()
