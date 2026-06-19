"""Convert every TIFF in examples/ to PNG in converted/, tagging each output
filename with the detected vendor (zeiss/hitachi)."""

from pathlib import Path

from PIL import Image

from parse_sem_file import detect_vendor

SRC_DIR = Path("examples")
OUT_DIR = Path("converted")


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    tifs = sorted(p for p in SRC_DIR.iterdir() if p.suffix.lower() in {".tif", ".tiff"})
    for tif in tifs:
        vendor = detect_vendor(str(tif))
        stem = tif.stem if tif.stem.startswith(vendor) else f"{vendor}_{tif.stem}"
        out = OUT_DIR / f"{stem}.png"
        with Image.open(tif) as img:
            img.save(out)
        print(f"converted {tif} -> {out}")


if __name__ == "__main__":
    main()
