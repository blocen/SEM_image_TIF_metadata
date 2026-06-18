"""Pydantic v2 model for Hitachi SEM (scanning electron microscope) image metadata.

Assumes the INI-style (INI = initialization) .txt sidecar and/or TIFF
(TIFF = tagged image file format) embedded metadata that Hitachi SEMs
(S-, SU-, Regulus, TM- series) write. Exact keys vary by model and firmware;
this captures the common, stable subset and retains anything unknown via
extra='allow'.

The "value+unit" strings Hitachi emits (e.g. "15.0kV", "8.5mm", "x50.0k") are
normalised to canonical units:
  - accelerating / deceleration voltage  -> V  (volt)
  - emission current                     -> uA (microampere)
  - working distance                     -> mm (millimetre)
  - pixel size                           -> nm (nanometre)
  - magnification                        -> dimensionless float
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class SignalType(str, Enum):
    """Detector / signal label. SE = secondary electron, BSE = backscattered electron."""

    SE = "SE"
    SE_UPPER = "SE(U)"
    SE_LOWER = "SE(L)"
    BSE = "BSE"
    BSE_COMPO = "BSE(COMPO)"
    BSE_TOPO = "BSE(TOPO)"
    MIX = "MIX"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value):  # lenient: unknown labels do not raise
        return cls.UNKNOWN


class VacuumMode(str, Enum):
    HIGH = "High"  # high vacuum
    LOW = "Low"  # low vacuum / variable pressure
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN


# --- unit parsing helpers ---------------------------------------------------

_NUM = re.compile(r"[+-]?\d+(?:\.\d+)?")


def _parse_quantity(raw, factors: dict[str, float]) -> Optional[float]:
    """Parse 'value+unit' into a canonical unit using `factors` (suffix -> multiplier)."""
    if raw is None or raw == "":
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip().lower().replace("µ", "u")
    m = _NUM.search(s)
    if not m:
        return None
    value = float(m.group())
    unit = s[m.end() :].strip()
    # match longest suffix first so 'mm'/'ma' beat 'm'/''
    for suffix in sorted(factors, key=len, reverse=True):
        if unit.startswith(suffix):
            return value * factors[suffix]
    return value  # no recognised unit -> assume already canonical


def _parse_magnification(raw) -> Optional[float]:
    """Parse Hitachi magnification: 'x50.0k', 'x1500', '50000' -> float."""
    if raw is None or raw == "":
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip().lower().lstrip("x").replace(",", "")
    m = _NUM.search(s)
    if not m:
        return None
    value = float(m.group())
    if "k" in s[m.end() :]:
        value *= 1000
    return value


_VOLTAGE = {"kv": 1000.0, "v": 1.0, "": 1.0}
_CURRENT = {
    "a": 1e6,
    "ma": 1e3,
    "ua": 1.0,
    "na": 1e-3,
    "": 1.0,
}  # canonical uA
_DISTANCE = {"mm": 1.0, "um": 1e-3, "m": 1e3, "": 1.0}  # canonical mm
_PIXEL = {"nm": 1.0, "um": 1e3, "pm": 1e-3, "m": 1e9, "": 1.0}  # canonical nm


# --- nested models ----------------------------------------------------------


class ImageDimensions(BaseModel):
    width: int = Field(description="pixels")
    height: int = Field(description="pixels")

    @field_validator("width", "height", mode="before")
    @classmethod
    def _coerce(cls, v):
        return int(v)


class StagePosition(BaseModel):
    """Optional stage coordinates. X/Y/Z in mm, R/T in degrees."""

    model_config = ConfigDict(populate_by_name=True)

    x_mm: Optional[float] = Field(
        None, validation_alias=AliasChoices("StageX", "StageX_mm")
    )
    y_mm: Optional[float] = Field(
        None, validation_alias=AliasChoices("StageY", "StageY_mm")
    )
    z_mm: Optional[float] = Field(
        None, validation_alias=AliasChoices("StageZ", "StageZ_mm")
    )
    rotation_deg: Optional[float] = Field(
        None, validation_alias=AliasChoices("StageR", "StageR_deg")
    )
    tilt_deg: Optional[float] = Field(
        None, validation_alias=AliasChoices("StageT", "StageT_deg")
    )


# --- main model -------------------------------------------------------------


class HitachiSEMImage(BaseModel):
    """Metadata for one image from a Hitachi SEM (scanning electron microscope)."""

    model_config = ConfigDict(
        populate_by_name=True,  # accept python names too, not only Hitachi aliases
        extra="allow",  # keep unknown firmware-specific keys instead of dropping
        str_strip_whitespace=True,
        use_enum_values=False,
    )

    # instrument / sample
    system_name: Optional[str] = Field(
        None, validation_alias=AliasChoices("SystemName", "InstructName")
    )
    serial_number: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("SerialNumber", "Instrument Serial"),
    )
    sample_name: Optional[str] = Field(
        None, validation_alias=AliasChoices("SampleName")
    )

    # acquisition timestamp (kept as raw strings: format varies by firmware,
    # commonly MM/DD/YYYY or YYYY/MM/DD)
    acquired_date: Optional[str] = Field(
        None, validation_alias=AliasChoices("Date", "Data")
    )
    acquired_time: Optional[str] = Field(
        None, validation_alias=AliasChoices("Time")
    )

    # beam conditions
    accelerating_voltage_v: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("AcceleratingVoltage", "AccVoltage"),
        description="AV (accelerating voltage), volts",
    )
    deceleration_voltage_v: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("DecelerationVoltage"),
        description="volts",
    )
    emission_current_ua: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("EmissionCurrent"),
        description="microampere",
    )

    # imaging geometry
    magnification: Optional[float] = Field(
        None, validation_alias=AliasChoices("Magnification")
    )
    working_distance_mm: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("WorkingDistance", "WD"),
        description="WD (working distance), millimetre",
    )

    # detector / environment
    signal: SignalType = Field(
        SignalType.UNKNOWN,
        validation_alias=AliasChoices("Signal", "SignalName"),
    )
    vacuum_mode: VacuumMode = Field(
        VacuumMode.UNKNOWN,
        validation_alias=AliasChoices("Vacuum", "VacuumMode"),
    )
    lens_mode: Optional[str] = Field(
        None, validation_alias=AliasChoices("LensMode")
    )

    # image data
    dimensions: Optional[ImageDimensions] = Field(
        None, validation_alias=AliasChoices("DataSize", "ImageSize")
    )
    pixel_size_nm: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("PixelSize"),
        description="nanometre per pixel",
    )
    scale_bar_um: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("MicronMarker", "Micron Marker"),
        description="micrometre",
    )
    scan_speed: Optional[str] = Field(
        None, validation_alias=AliasChoices("ScanSpeed")
    )
    brightness: Optional[float] = Field(
        None, validation_alias=AliasChoices("Brightness")
    )
    contrast: Optional[float] = Field(
        None, validation_alias=AliasChoices("Contrast")
    )

    stage: Optional[StagePosition] = None

    # --- validators ---------------------------------------------------------

    @field_validator(
        "accelerating_voltage_v", "deceleration_voltage_v", mode="before"
    )
    @classmethod
    def _v(cls, raw):
        return _parse_quantity(raw, _VOLTAGE)

    @field_validator("emission_current_ua", mode="before")
    @classmethod
    def _ua(cls, raw):
        return _parse_quantity(raw, _CURRENT)

    @field_validator("working_distance_mm", mode="before")
    @classmethod
    def _wd(cls, raw):
        return _parse_quantity(raw, _DISTANCE)

    @field_validator("pixel_size_nm", "scale_bar_um", mode="before")
    @classmethod
    def _len(cls, raw):
        # scale bar usually given in um already; pixel size handled by _PIXEL map
        return _parse_quantity(
            raw,
            _PIXEL
            if raw and "nm" in str(raw).lower()
            else {"um": 1.0, "nm": 1e-3, "": 1.0},
        )

    @field_validator("magnification", mode="before")
    @classmethod
    def _mag(cls, raw):
        return _parse_magnification(raw)

    @field_validator("dimensions", mode="before")
    @classmethod
    def _dims(cls, raw):
        if isinstance(raw, str):
            m = re.match(r"\s*(\d+)\s*[x×]\s*(\d+)", raw)
            if m:
                return {"width": int(m.group(1)), "height": int(m.group(2))}
            return None
        return raw


if __name__ == "__main__":
    # example: a flat dict as produced by parsing a Hitachi .txt sidecar
    raw = {
        "SystemName": "SU8230",
        "SerialNumber": "123456",
        "SampleName": "specimen_A",
        "Date": "06/18/2026",
        "Time": "14:32:05",
        "AcceleratingVoltage": "15.0kV",
        "EmissionCurrent": "10.0uA",
        "Magnification": "x50.0k",
        "WorkingDistance": "8.5mm",
        "Signal": "SE(U)",
        "Vacuum": "High",
        "DataSize": "1280x960",
        "PixelSize": "2.5nm",
        "MicronMarker": "1.00um",
        "StageX": "12.34",
        "SomeUnknownFirmwareKey": "kept_via_extra_allow",
    }
    img = HitachiSEMImage.model_validate(raw)
    img.stage = StagePosition.model_validate(
        raw
    )  # stage parsed separately if flat
    print(img.model_dump_json(indent=2))
    print("extra kept:", img.model_extra)
