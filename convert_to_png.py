"""Convert every TIFF in examples/ to PNG in converted/."""

from pathlib import Path

from PIL import Image

SRC_DIR = Path("examples")
OUT_DIR = Path("converted")


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    tifs = sorted(p for p in SRC_DIR.iterdir() if p.suffix.lower() in {".tif", ".tiff"})
    for tif in tifs:
        out = OUT_DIR / f"{tif.stem}.png"
        with Image.open(tif) as img:
            img.save(out)
        print(f"converted {tif} -> {out}")


if __name__ == "__main__":
    main()
