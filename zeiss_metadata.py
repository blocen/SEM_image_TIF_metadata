"""Pydantic model for Zeiss SEM metadata stored in the CZ_SEM TIFF tag (34118).

tifffile decodes that tag into a dict of `key -> (label, value[, unit])`, where
values are already numeric and units are already separated. The parser flattens
each entry to `key -> value`; this model maps the useful subset by its CZ_SEM
key. Units are whatever the instrument reported (kV, mm, nm, µA, mbar) and are
documented per field. Unknown keys are dropped.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _parse_mag(raw) -> Optional[float]:
    """Zeiss magnification arrives as '50.00 K X' / '1.50 M X' / '157 X'."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).upper().replace("X", "").strip()
    mult = 1.0
    if "K" in s:
        mult, s = 1e3, s.replace("K", "")
    elif "M" in s:
        mult, s = 1e6, s.replace("M", "")
    return float(s.strip()) * mult


class ZeissSEMMetadata(BaseModel):
    """Metadata for one image from a Zeiss SEM (CZ_SEM tag)."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    # instrument / sample
    serial_number: Optional[str] = Field(None, alias="sv_serial_number")
    image_path: Optional[str] = Field(None, alias="sv_image_path")

    # acquisition timestamp (assembled from ap_date + ap_time below)
    capture_date: Optional[datetime] = None

    # beam conditions
    accelerating_voltage_kv: float = Field(..., alias="ap_actualkv")
    beam_current_ua: Optional[float] = Field(None, alias="ap_beam_current")
    aperture_size_um: Optional[float] = Field(None, alias="ap_aperturesize")

    # imaging geometry
    magnification: float = Field(..., alias="ap_mag")
    working_distance_mm: float = Field(..., alias="ap_wd")
    pixel_size_nm: float = Field(..., alias="ap_image_pixel_size")

    # detector / environment
    detector: Optional[str] = Field(None, alias="dp_detector_type")
    signal: Optional[str] = Field(None, alias="dp_detector_channel")
    gun_vacuum_mbar: Optional[float] = Field(None, alias="ap_column_vac")
    store_resolution: Optional[str] = Field(None, alias="dp_image_store")

    # stage position (X/Y/Z in mm, T/R in degrees)
    stage_x_mm: Optional[float] = Field(None, alias="ap_stage_at_x")
    stage_y_mm: Optional[float] = Field(None, alias="ap_stage_at_y")
    stage_z_mm: Optional[float] = Field(None, alias="ap_stage_at_z")
    stage_tilt_deg: Optional[float] = Field(None, alias="ap_stage_at_t")
    stage_rotation_deg: Optional[float] = Field(None, alias="ap_stage_at_r")

    @field_validator("magnification", mode="before")
    @classmethod
    def _mag(cls, raw):
        return _parse_mag(raw)

    @model_validator(mode="before")
    @classmethod
    def _assemble_date(cls, data):
        # Zeiss stores e.g. ap_date='18 Jul 2019', ap_time='10:09:27'.
        if isinstance(data, dict) and "capture_date" not in data:
            date, time = data.get("ap_date"), data.get("ap_time")
            if date and time:
                try:
                    data = {
                        **data,
                        "capture_date": datetime.strptime(
                            f"{date} {time}", "%d %b %Y %H:%M:%S"
                        ),
                    }
                except ValueError:
                    pass
        return data
