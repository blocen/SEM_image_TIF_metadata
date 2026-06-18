"""Generate example Hitachi-style SEM TIFFs for testing parse_sem_file.

Real Hitachi SEMs embed an INI-style metadata block in the TIFF
ImageDescription (tag 270). These synthetic files reproduce that layout so
the parser and SEMMetadata model can be exercised without proprietary files.
"""

import numpy as np
from tifffile import imwrite

EXAMPLES = [
    {
        "Condition.Lens.MachineNo": "SU8230",
        "Condition.Screen.Date": "2026/06/18 14:32:05",
        "Condition.Screen.Operator": "A. Tanaka",
        "Condition.Lens.AcceleratingVoltage": "15.0 kV",
        "Condition.Lens.EmissionCurrent": "10.0 uA",
        "Condition.Lens.Magnification": "50000",
        "Condition.Lens.Wd": "8.5 mm",
        "Condition.Lens.ProbeCurrent": "Normal",
        "Condition.Screen.SignalName": "SE",
        "Condition.Stage.X": "12.34 mm",
        "Condition.Stage.Y": "5.67 mm",
        "Condition.Stage.Z": "3.10 mm",
        "Condition.Stage.T": "0.0 deg",
        "Condition.Stage.R": "0.0 deg",
        "Condition.Vacuum.VacuumMode": "High Vacuum",
        "Condition.Screen.PixelSize": "2.5 nm",
    },
    {
        "Condition.Lens.MachineNo": "SU9000",
        "Condition.Screen.Date": "2026/05/01 09:15:42",
        "Condition.Screen.Operator": "R. Singh",
        "Condition.Lens.AcceleratingVoltage": "5.0 kV",
        "Condition.Lens.EmissionCurrent": "7.2 uA",
        "Condition.Lens.Magnification": "120000",
        "Condition.Lens.Wd": "4.2 mm",
        "Condition.Screen.SignalName": "InBeam",
        "Condition.Stage.X": "-3.50 mm",
        "Condition.Stage.Y": "1.20 mm",
        "Condition.Stage.Z": "2.05 mm",
        "Condition.Stage.T": "15.0 deg",
        "Condition.Stage.R": "90.0 deg",
        "Condition.Vacuum.VacuumMode": "High Vacuum",
        "Condition.Screen.PixelSize": "0.8 nm",
    },
    {
        "Condition.Lens.MachineNo": "FlexSEM 1000",
        "Condition.Screen.Date": "2026/06/10 17:48:11",
        "Condition.Lens.AcceleratingVoltage": "20.0 kV",
        "Condition.Lens.EmissionCurrent": "45.0 uA",
        "Condition.Lens.Magnification": "1500",
        "Condition.Lens.Wd": "10.0 mm",
        "Condition.Screen.SignalName": "BSE",
        "Condition.Stage.X": "0.00 mm",
        "Condition.Stage.Y": "0.00 mm",
        "Condition.Stage.Z": "12.50 mm",
        "Condition.Vacuum.VacuumMode": "Low Vacuum",
        "Condition.Vacuum.Pressure": "30.0 Pa",
        "Condition.Screen.PixelSize": "85.0 nm",
    },
]


def _to_ini(meta: dict) -> str:
    """Render a flat 'Section.Key' dict back into the sectioned INI block."""
    sections: dict[str, list[tuple[str, str]]] = {}
    for full_key, value in meta.items():
        section, _, key = full_key.rpartition(".")
        sections.setdefault(section, []).append((key, value))
    lines = []
    for section, pairs in sections.items():
        lines.append(f"[{section}]")
        lines.extend(f"{key}={value}" for key, value in pairs)
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    rng = np.random.default_rng(0)
    for i, meta in enumerate(EXAMPLES, start=1):
        image = rng.integers(0, 256, size=(480, 640), dtype=np.uint8)
        path = f"examples/hitachi_example_{i}.tif"
        imwrite(path, image, description=_to_ini(meta))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
