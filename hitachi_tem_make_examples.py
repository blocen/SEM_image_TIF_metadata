"""Generate example Hitachi TEM images and a .txt sidecar for testing
hitachi_tem_metadata.

Hitachi transmission electron microscopes (HT7700 / HT7800) write a flat
key=value ``.txt`` sidecar next to each saved image and embed the same block in
the TIFF ImageDescription (tag 270). These synthetic files reproduce that layout
so HitachiTEMMetadata can be exercised without proprietary files. Field values
are representative (e.g. 40-120 kV, HC/HR modes) but not from a real instrument.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from tifffile import imwrite

EXAMPLES = [
    {
        "Instrument": "HT7700",
        "SerialNumber": "HT77-1234",
        "DataNumber": "000123",
        "ImageName": "hitachi_tem_example_1.tif",
        "Directory": "C:\\Users\\TEM\\Data\\",
        "SampleName": "Carbon nanotubes",
        "Operator": "A. Tanaka",
        "Date": "18/06/2026",
        "Time": "14:32:05",
        "AccVoltage": "100 kV",
        "EmissionCurrent": "8.5 uA",
        "FilamentValue": "2.30",
        "Mode": "HC",
        "Magnification": "50000",
        "SpotSize": "2",
        "CondenserAperture": "2",
        "ObjectiveAperture": "3",
        "Brightness": "128",
        "Contrast": "140",
        "Gamma": "1.00",
        "Camera": "AMT XR81",
        "ExposureTime": "500 ms",
        "Binning": "1",
        "ImageSize": "2048x2048",
        "PixelSize": "0.45 nm",
        "MicronMarker": "200 nm",
        "StageX": "125.3 um",
        "StageY": "-42.7 um",
        "StageZ": "10.0 um",
        "TiltX": "3.5 deg",
        "TiltY": "0.0 deg",
        "ColumnPressure": "1.2e-5 Pa",
        "Comment": "",
    },
    {
        "Instrument": "HT7800",
        "SerialNumber": "HT78-0042",
        "DataNumber": "000045",
        "ImageName": "hitachi_tem_example_2.tif",
        "Directory": "D:\\Sessions\\2026\\",
        "SampleName": "Liver tissue section",
        "Operator": "R. Singh",
        "Date": "01/05/2026",
        "Time": "09:15:42",
        "AccVoltage": "120 kV",
        "EmissionCurrent": "12.0 uA",
        "FilamentValue": "2.55",
        "Mode": "HR",
        "Magnification": "200000",
        "SpotSize": "1",
        "CondenserAperture": "1",
        "ObjectiveAperture": "2",
        "Brightness": "110",
        "Contrast": "155",
        "Gamma": "1.10",
        "Camera": "EMSIS Xarosa",
        "ExposureTime": "200 ms",
        "Binning": "2",
        "ImageSize": "4096x4096",
        "PixelSize": "0.12 nm",
        "MicronMarker": "50 nm",
        "StageX": "-3.5 um",
        "StageY": "1.2 um",
        "StageZ": "2.05 um",
        "TiltX": "15.0 deg",
        "TiltY": "-5.0 deg",
        "ColumnPressure": "8.0e-6 Pa",
        "Comment": "",
    },
    {
        "Instrument": "HT7700",
        "SerialNumber": "HT77-1234",
        "DataNumber": "000124",
        "ImageName": "hitachi_tem_example_3.tif",
        "Directory": "C:\\Users\\TEM\\Data\\",
        "SampleName": "Gold nanoparticles",
        "Operator": "A. Tanaka",
        "Date": "10/06/2026",
        "Time": "17:48:11",
        "AccVoltage": "80 kV",
        "EmissionCurrent": "6.8 uA",
        "FilamentValue": "2.10",
        "Mode": "HC",
        "Magnification": "8000",
        "SpotSize": "3",
        "CondenserAperture": "3",
        "ObjectiveAperture": "0",
        "Brightness": "135",
        "Contrast": "125",
        "Gamma": "1.00",
        "Camera": "AMT XR81",
        "ExposureTime": "1000 ms",
        "Binning": "1",
        "ImageSize": "2048x2048",
        "PixelSize": "2.8 nm",
        "MicronMarker": "1000 nm",
        "StageX": "0.0 um",
        "StageY": "0.0 um",
        "StageZ": "12.5 um",
        "TiltX": "0.0 deg",
        "TiltY": "0.0 deg",
        "ColumnPressure": "1.5e-5 Pa",
        "Comment": "",
    },
]


def _to_block(meta: dict) -> str:
    """Render a flat dict as the key=value metadata block."""
    return "\n".join(f"{key}={value}" for key, value in meta.items())


def _micrograph(rng, size: int = 640) -> np.ndarray:
    """A synthetic TEM-style frame: dark particles on a light field with grain.

    Not a real micrograph, but visually closer to one than uniform noise.
    """
    img = Image.new("L", (size, size), color=205)
    draw = ImageDraw.Draw(img)
    for _ in range(int(rng.integers(45, 90))):
        r = int(rng.integers(5, 28))
        x, y = int(rng.integers(0, size)), int(rng.integers(0, size))
        shade = int(rng.integers(25, 95))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=shade)
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    arr = np.asarray(img).astype(np.int16)
    arr += rng.integers(-12, 13, size=arr.shape, dtype=np.int16)  # detector grain
    return np.clip(arr, 0, 255).astype(np.uint8)


def main() -> None:
    rng = np.random.default_rng(0)
    for i, meta in enumerate(EXAMPLES, start=1):
        image = _micrograph(rng)
        block = _to_block(meta)

        tif_path = f"examples/hitachi_tem_example_{i}.tif"
        imwrite(tif_path, image, description=block)
        print(f"wrote {tif_path}")

        # The first example also ships its standalone .txt sidecar.
        if i == 1:
            txt_path = "examples/hitachi_tem_example.txt"
            with open(txt_path, "w", encoding="utf-8") as fh:
                fh.write(block + "\n")
            print(f"wrote {txt_path}")


if __name__ == "__main__":
    main()
