import re
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Aliases whose raw values carry trailing units ("15.0 kV") and must be
# reduced to a bare number. Matched exactly so textual keys that merely
# contain a fragment (e.g. ProbeCurrent, MachineNo) are left untouched.
_NUMERIC_KEYS = frozenset(
    {
        "Condition.Lens.AcceleratingVoltage",
        "Condition.Lens.EmissionCurrent",
        "Condition.Lens.Wd",
        "Condition.Stage.X",
        "Condition.Stage.Y",
        "Condition.Stage.Z",
        "Condition.Stage.T",
        "Condition.Stage.R",
        "Condition.Screen.PixelSize",
        "Condition.Vacuum.Pressure",
    }
)


class SEMMetadata(BaseModel):
    """
    Pydantic validation model tailored explicitly for Hitachi SEM systems
    (e.g., SU8000, SU9000, FlexSEM series). Handles embedded TIFF string formatting.
    """

    # System & Operator Info
    model_name: str = Field(..., alias="Condition.Lens.MachineNo")
    capture_date: datetime = Field(..., alias="Condition.Screen.Date")
    operator: Optional[str] = Field(None, alias="Condition.Screen.Operator")

    # Column / Beam Controls
    accelerating_voltage_kv: float = Field(
        ..., alias="Condition.Lens.AcceleratingVoltage"
    )
    emission_current_ua: float = Field(
        ..., alias="Condition.Lens.EmissionCurrent"
    )
    magnification: int = Field(..., alias="Condition.Lens.Magnification")
    working_distance_mm: float = Field(..., alias="Condition.Lens.Wd")
    probe_current_mode: Optional[str] = Field(
        None, alias="Condition.Lens.ProbeCurrent"
    )

    # Detector Settings
    detector_signal: Literal[
        "SE", "BSE", "LA-BSE", "HA-BSE", "InBeam", "EDS"
    ] = Field(..., alias="Condition.Screen.SignalName")

    # 5-Axis Stage Positioning
    stage_x_mm: float = Field(..., alias="Condition.Stage.X")
    stage_y_mm: float = Field(..., alias="Condition.Stage.Y")
    stage_z_mm: float = Field(..., alias="Condition.Stage.Z")
    stage_tilt_deg: float = Field(0.0, alias="Condition.Stage.T")
    stage_rotation_deg: float = Field(0.0, alias="Condition.Stage.R")

    # Vacuum Environment
    vacuum_mode: Literal["High Vacuum", "Low Vacuum", "VP"] = Field(
        "High Vacuum", alias="Condition.Vacuum.VacuumMode"
    )
    chamber_pressure_pa: Optional[float] = Field(
        None, alias="Condition.Vacuum.Pressure"
    )

    # Calibration
    pixel_size_nm: float = Field(..., alias="Condition.Screen.PixelSize")

    @model_validator(mode="before")
    @classmethod
    def clean_sem_strings(cls, data) -> dict:
        """
        Coerces text strings containing units ('mm', 'deg', 'kV', 'uA')
        and maps messy labels before passing to validation fields.
        """
        if isinstance(data, dict):
            cleaned = {}
            for key, val in data.items():
                if not isinstance(val, str):
                    cleaned[key] = val
                    continue

                val_strip = val.strip()

                # Extract numbers out of trailing unit strings
                if key in _NUMERIC_KEYS:
                    # Capture floating points/scientific notation from strings
                    num_match = re.search(r"[-+]?\d*\.\d+|\d+", val_strip)
                    cleaned[key] = (
                        float(num_match.group()) if num_match else None
                    )
                elif "Date" in key:
                    try:
                        # Common Hitachi timestamp translation: YYYY/MM/DD HH:MM:SS
                        cleaned[key] = datetime.strptime(
                            val_strip, "%Y/%m/%d %H:%M:%S"
                        )
                    except ValueError:
                        cleaned[key] = val_strip
                else:
                    cleaned[key] = val_strip
            return cleaned
        return data

    model_config = ConfigDict(populate_by_name=True)
