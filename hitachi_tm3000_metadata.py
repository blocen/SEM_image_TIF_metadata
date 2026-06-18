import re
from datetime import date, time
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Keys whose raw values carry a trailing unit ("15000 Volt", "6900 um") and
# must be reduced to a bare number before validation.
_UNIT_KEYS = frozenset(
    {
        "AcceleratingVoltage",
        "DecelerationVoltage",
        "WorkingDistance",
        "EmissionCurrent",
        "FilamentCurrent",
        "SpecimenBias",
    }
)

# Keys storing a "Yes"/"No" flag.
_BOOL_KEYS = frozenset(
    {
        "DateCheck",
        "TimeCheck",
        "NumberCheck",
        "CommentCheck",
        "DigitalZoom",
    }
)


class TM3000Metadata(BaseModel):
    """
    Pydantic model for the flat INI-style metadata block emitted by Hitachi
    TM3000 tabletop SEMs (the SEMImageFile.txt sidecar / embedded TIFF text).

    Unlike SEMMetadata, keys are flat (no [section] prefixes) and numeric
    fields embed their unit in the value string.
    """

    model_config = ConfigDict(populate_by_name=True)

    # File / system identity
    version: str = Field(..., alias="Version")
    instrument_name: str = Field(..., alias="InstructName")
    serial_number: str = Field(..., alias="SerialNumber")
    data_number: str = Field(..., alias="DataNumber")  # zero-padded, keep as str
    sample_name: Optional[str] = Field(None, alias="SampleName")
    image_format: str = Field(..., alias="Format")
    image_name: str = Field(..., alias="ImageName")
    directory: str = Field(..., alias="Directory")
    save_mode: int = Field(..., alias="SaveMode")
    media: str = Field(..., alias="Media")

    # Acquisition timestamp (Date is DD/MM/YYYY)
    acquisition_date: date = Field(..., alias="Date")
    acquisition_time: time = Field(..., alias="Time")

    # Capture flags
    date_check: bool = Field(..., alias="DateCheck")
    time_check: bool = Field(..., alias="TimeCheck")
    number_check: bool = Field(..., alias="NumberCheck")
    comment_check: bool = Field(..., alias="CommentCheck")
    digital_zoom: bool = Field(..., alias="DigitalZoom")

    # Image geometry / calibration
    data_size: str = Field(..., alias="DataSize")  # e.g. "1280x1100"
    dpi: float = Field(..., alias="DPI")
    pixel_size_nm: float = Field(..., alias="PixelSize")
    micron_marker_nm: Optional[int] = Field(None, alias="MicronMarker")

    # Column / beam
    signal_name: str = Field(..., alias="SignalName")
    accelerating_voltage_v: float = Field(..., alias="AcceleratingVoltage")
    deceleration_voltage_v: Optional[float] = Field(None, alias="DecelerationVoltage")
    magnification: int = Field(..., alias="Magnification")
    working_distance_um: float = Field(..., alias="WorkingDistance")
    emission_current_na: float = Field(..., alias="EmissionCurrent")
    filament_current_ma: float = Field(..., alias="FilamentCurrent")
    condenser2: Optional[int] = Field(None, alias="Condencer2")  # sic in source
    specimen_bias: Optional[float] = Field(None, alias="SpecimenBias")

    # Display / detector settings
    observation_condition: Optional[str] = Field(None, alias="ObservationCondition")
    brightness: Optional[int] = Field(None, alias="Brightness")
    contrast: Optional[int] = Field(None, alias="Contrast")
    rotation: Optional[int] = Field(None, alias="Rotation")
    lens_mode: Optional[str] = Field(None, alias="LensMode")
    photo_size: Optional[str] = Field(None, alias="PhotoSize")
    vacuum: str = Field(..., alias="Vacuum")
    scan_speed: Optional[str] = Field(None, alias="ScanSpeed")
    calibration_scan_speed: Optional[str] = Field(None, alias="CalibrationScanSpeed")
    color_mode: Optional[str] = Field(None, alias="ColorMode")
    color_palette: Optional[str] = Field(None, alias="ColorPalette")
    screen_mode: Optional[str] = Field(None, alias="ScreenMode")

    # Sub channel
    sub_magnification: Optional[int] = Field(None, alias="SubMagnification")
    sub_signal_name: Optional[str] = Field(None, alias="SubSignalName")

    # Annotations
    comment: Optional[str] = Field(None, alias="Comment")
    keyword1: Optional[str] = Field(None, alias="KeyWord1")
    keyword2: Optional[str] = Field(None, alias="KeyWord2")
    condition: Optional[str] = Field(None, alias="Condition")
    data_display_combine: Optional[str] = Field(None, alias="DataDisplayCombine")

    # Stage
    stage_type: Optional[int] = Field(None, alias="StageType")
    stage_position_x: Optional[float] = Field(None, alias="StagePositionX")
    stage_position_y: Optional[float] = Field(None, alias="StagePositionY")
    stage_position_r: Optional[float] = Field(None, alias="StagePositionR")
    stage_position_z: Optional[float] = Field(None, alias="StagePositionZ")
    stage_position_t: Optional[float] = Field(None, alias="StagePositionT")

    @model_validator(mode="before")
    @classmethod
    def clean_values(cls, data) -> dict:
        """Strip units, normalise Yes/No flags, and treat blanks as missing."""
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
            elif key in _BOOL_KEYS:
                cleaned[key] = val.lower() == "yes"
            elif key in _UNIT_KEYS:
                m = re.search(r"[-+]?\d*\.?\d+", val)
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
    def data_width(self) -> int:
        return int(self.data_size.split("x")[0])

    @property
    def data_height(self) -> int:
        return int(self.data_size.split("x")[1])

    @classmethod
    def from_file(cls, filepath: str) -> "TM3000Metadata":
        """Parse a flat ``key=value`` SEMImageFile.txt sidecar."""
        raw = {}
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                raw[key.strip()] = val.strip()
        return cls.model_validate(raw)


if __name__ == "__main__":
    meta = TM3000Metadata.from_file("examples/hitachi_tm3000_example.txt")
    print(meta.model_dump_json(indent=2))
    print(f"\n{meta.data_width} x {meta.data_height} px")
