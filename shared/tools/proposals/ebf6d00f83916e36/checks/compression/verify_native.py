"""Verify the saved census through the supplied native receipt reader."""
from pathlib import Path
import hashlib
import json

from arcpuzzles.receipt_input import read_receipt

root = Path(__file__).resolve().parent.parent
source = root / "lesson-census.json"
original = source.read_bytes() if source.is_file() else None
raw = None
for filename in ("lesson-census.json.gz", "lesson-census.compression.json"):
    decoded = read_receipt(root / filename)
    if raw is None:
        raw = decoded["raw"]
    assert decoded["raw"] == raw
    assert decoded["transport"]["format"] == "arcpuzzles-evidence-gzip-v1"
if original is not None:
    assert original == raw
print(json.dumps({
    "status": "verified",
    "original_present": original is not None,
    "original_matches_when_present": original == raw if original is not None else None,
    "raw_bytes": len(raw),
    "raw_sha256": hashlib.sha256(raw).hexdigest(),
    "native_reader_entrypoints_verified": ["lesson-census.json.gz", "lesson-census.compression.json"],
}, indent=2))
