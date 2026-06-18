from typing import Union

from tifffile import TiffFile

from SEMMetadata import SEMMetadata
from ZeissSEMMetadata import ZeissSEMMetadata

SemMetadata = Union[SEMMetadata, ZeissSEMMetadata]

# Vendor-specific TIFF tags carrying the embedded metadata.
CZ_SEM_TAG = 34118  # Zeiss: structured dict of key -> (label, value[, unit])
HITACHI_TAGS = (37888, 34118, 270)  # Hitachi: INI text in one of these


def _parse_zeiss(tif: TiffFile) -> ZeissSEMMetadata:
    cz = tif.pages[0].tags[CZ_SEM_TAG].value
    # Flatten key -> (label, value[, unit]) to key -> value.
    flat = {
        key: entry[1]
        for key, entry in cz.items()
        if key and isinstance(entry, (tuple, list)) and len(entry) >= 2
    }
    return ZeissSEMMetadata.model_validate(flat)


def _parse_hitachi(tif: TiffFile) -> SEMMetadata:
    hitachi_raw_text = None
    for page in tif.pages:
        for tag_id in HITACHI_TAGS:
            if tag_id in page.tags:
                tag_value = page.tags[tag_id].value
                if isinstance(tag_value, str) and "Condition." in tag_value:
                    hitachi_raw_text = tag_value
                    break
        if hitachi_raw_text:
            break

    if not hitachi_raw_text:
        raise ValueError("No Hitachi metadata block found")

    # --- Inline Text-to-Dict Parsing Engine ---
    extracted_dict = {}
    current_section = ""

    for line in hitachi_raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Track INI sections like [Condition.Lens]
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1] + "."
            continue

        if "=" in line:
            key, val = line.split("=", 1)
            full_key = (
                f"{current_section}{key.strip()}"
                if current_section
                else key.strip()
            )
            extracted_dict[full_key] = val.strip()

    return SEMMetadata.model_validate(extracted_dict)


def parse_sem_file(filepath: str) -> SemMetadata:
    """Parse a Hitachi or Zeiss SEM TIFF, dispatching on the embedded metadata."""
    with TiffFile(filepath) as tif:
        cz = tif.pages[0].tags.get(CZ_SEM_TAG)
        if cz is not None and isinstance(cz.value, dict):
            return _parse_zeiss(tif)
        return _parse_hitachi(tif)


if __name__ == "__main__":
    import glob

    paths = sorted(glob.glob("examples/*.tif"))
    if not paths:
        raise SystemExit("No examples found. Run: python make_examples.py")

    for path in paths:
        print(f"\n=== {path} ===")
        try:
            print(parse_sem_file(path).model_dump_json(indent=2))
        except Exception as e:
            print(f"FAILED: {e}")
