import re
from datetime import date, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from tifffile import TiffFile

# Keys whose raw values carry a trailing unit ("100 kV", "0.45 nm", "1.2e-5 Pa")
# and must be reduced to a bare number before validation.
_UNIT_KEYS = frozenset(
    {
        "AccVoltage",
        "EmissionCurrent",
        "ExposureTime",
        "PixelSize",
        "MicronMarker",
        "StageX",
        "StageY",
        "StageZ",
        "TiltX",
        "TiltY",
        "ColumnPressure",
    }
)

# Number, optionally signed, decimal, with optional scientific exponent
# (column pressures are written like "1.2e-5 Pa").
_NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


class HitachiTEMMetadata(BaseModel):
    """
    Pydantic model for the flat key=value metadata block emitted by Hitachi
    transmission electron microscopes (HT7700 / HT7800 series).

    The instrument writes a ``.txt`` sidecar next to each saved image and also
    embeds the same block in the TIFF ImageDescription (tag 270). Keys are flat
    (no [section] prefixes, unlike the SU-series SEMs) and numeric fields embed
    their unit in the value string ("100 kV", "0.45 nm").
    """

    model_config = ConfigDict(populate_by_name=True)

    # File / system identity
    instrument: str = Field(..., alias="Instrument")
    serial_number: Optional[str] = Field(None, alias="SerialNumber")
    data_number: Optional[str] = Field(None, alias="DataNumber")  # zero-padded
    image_name: str = Field(..., alias="ImageName")
    directory: Optional[str] = Field(None, alias="Directory")
    sample_name: Optional[str] = Field(None, alias="SampleName")
    operator: Optional[str] = Field(None, alias="Operator")

    # Acquisition timestamp (Date is DD/MM/YYYY, Time is HH:MM:SS)
    acquisition_date: date = Field(..., alias="Date")
    acquisition_time: time = Field(..., alias="Time")

    # Column / beam
    accelerating_voltage_kv: float = Field(..., alias="AccVoltage")
    emission_current_ua: Optional[float] = Field(None, alias="EmissionCurrent")
    filament_value: Optional[float] = Field(None, alias="FilamentValue")
    imaging_mode: str = Field(..., alias="Mode")  # "HC" (contrast) / "HR" (resolution)
    magnification: int = Field(..., alias="Magnification")
    spot_size: Optional[int] = Field(None, alias="SpotSize")
    condenser_aperture: Optional[int] = Field(None, alias="CondenserAperture")
    objective_aperture: Optional[int] = Field(None, alias="ObjectiveAperture")

    # Display
    brightness: Optional[int] = Field(None, alias="Brightness")
    contrast: Optional[int] = Field(None, alias="Contrast")
    gamma: Optional[float] = Field(None, alias="Gamma")

    # Camera / detector
    camera: Optional[str] = Field(None, alias="Camera")
    exposure_time_ms: Optional[float] = Field(None, alias="ExposureTime")
    binning: Optional[int] = Field(None, alias="Binning")
    image_size: str = Field(..., alias="ImageSize")  # e.g. "2048x2048"

    # Calibration
    pixel_size_nm: float = Field(..., alias="PixelSize")
    micron_marker_nm: Optional[float] = Field(None, alias="MicronMarker")

    # Goniometer stage
    stage_x_um: Optional[float] = Field(None, alias="StageX")
    stage_y_um: Optional[float] = Field(None, alias="StageY")
    stage_z_um: Optional[float] = Field(None, alias="StageZ")
    tilt_x_deg: Optional[float] = Field(None, alias="TiltX")
    tilt_y_deg: Optional[float] = Field(None, alias="TiltY")

    # Vacuum
    column_pressure_pa: Optional[float] = Field(None, alias="ColumnPressure")

    # Annotation
    comment: Optional[str] = Field(None, alias="Comment")

    @model_validator(mode="before")
    @classmethod
    def clean_values(cls, data) -> dict:
        """Strip units, and treat blank values as missing."""
        if not isinstance(data, dict):
            return data

        cleaned = {}
        for key, val in data.items():
            if not isinstance(val, str):
                cleaned[key] = val
                continue

            val = val.strip()
            if val == "" or val == "[]":
                cleaned[key] = None
            elif key in _UNIT_KEYS:
                m = _NUM_RE.search(val)
                cleaned[key] = float(m.group()) if m else None
            else:
                cleaned[key] = val
        return cleaned

    @field_validator("acquisition_date", mode="before")
    @classmethod
    def parse_date(cls, val):
        if isinstance(val, str):
            d, m, y = (int(p) for p in val.split("/"))
            return date(y, m, d)
        return val

    @field_validator("acquisition_time", mode="before")
    @classmethod
    def parse_time(cls, val):
        if isinstance(val, str):
            h, mi, s = (int(p) for p in val.split(":"))
            return time(h, mi, s)
        return val

    @property
    def image_width(self) -> int:
        return int(self.image_size.split("x")[0])

    @property
    def image_height(self) -> int:
        return int(self.image_size.split("x")[1])

    @staticmethod
    def _parse_block(text: str) -> dict:
        raw = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, val = line.split("=", 1)
            raw[key.strip()] = val.strip()
        return raw

    @classmethod
    def from_file(cls, filepath: str) -> "HitachiTEMMetadata":
        """Parse a flat ``key=value`` ``.txt`` sidecar."""
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            return cls.model_validate(cls._parse_block(fh.read()))

    @classmethod
    def from_tiff(cls, filepath: str) -> "HitachiTEMMetadata":
        """Parse the metadata block embedded in the TIFF ImageDescription."""
        with TiffFile(filepath) as tif:
            desc = tif.pages[0].tags.get(270)
            if desc is None or not isinstance(desc.value, str):
                raise ValueError("No ImageDescription metadata block found")
            return cls.model_validate(cls._parse_block(desc.value))


if __name__ == "__main__":
    meta = HitachiTEMMetadata.from_file("examples/hitachi_tem_example.txt")
    print(meta.model_dump_json(indent=2))
    print(f"\n{meta.image_width} x {meta.image_height} px")
