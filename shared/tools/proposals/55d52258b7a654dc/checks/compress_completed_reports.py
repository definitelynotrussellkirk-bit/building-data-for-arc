"""Compress completed JSON evidence with exact restoration and integrity metadata.

Usage: python3 compress_completed_reports.py PATH.json [PATH.json ...]
Run only after all writers and consumers of the original paths have finished.
Each source gets PATH.json.gz and PATH.compression.json. The source is removed
only after gzip round-trip and both SHA-256 values have been checked.
"""
import gzip
import hashlib
import json
from pathlib import Path
import sys


def compress(path):
    if path.is_symlink() or not path.is_file() or path.suffix != ".json":
        raise ValueError(f"Expected regular completed JSON: {path}")
    raw = path.read_bytes()
    report = json.loads(raw)
    if report.get("status") in ("running", "pending", "in_progress"):
        raise ValueError(f"Report is unfinished: {path}")
    packed_path = path.with_suffix(".json.gz")
    manifest_path = path.with_suffix(".compression.json")
    if packed_path.exists() or manifest_path.exists():
        raise FileExistsError(f"Preserve earlier compression: {path}")
    packed = gzip.compress(raw, mtime=0)
    assert gzip.decompress(packed) == raw
    sha = lambda value: hashlib.sha256(value).hexdigest()
    manifest = {"schema": "arcpuzzles-evidence-gzip-v1", "compression": "gzip",
                "report_schema": report.get("schema"), "status": report.get("status"),
                "training_admitted": False,
                "restore_argv": ["python3", "-m", "gzip", "-d", packed_path.name],
                "restore_note": "Restore a copy in a new directory; check raw_size and raw_sha256 before use.",
                "files": [{"path": path.name, "compressed_path": packed_path.name,
                           "raw_size": len(raw), "raw_sha256": sha(raw),
                           "compressed_size": len(packed), "compressed_sha256": sha(packed)}]}
    with packed_path.open("xb") as stream:
        stream.write(packed)
    with manifest_path.open("x") as stream:
        stream.write(json.dumps(manifest, indent=2) + "\n")
    assert gzip.decompress(packed_path.read_bytes()) == raw
    assert json.loads(manifest_path.read_text()) == manifest
    path.unlink()
    return {"source": str(path), "compressed": str(packed_path),
            "manifest": str(manifest_path), "raw_bytes": len(raw), "compressed_bytes": len(packed)}


if __name__ == "__main__":
    print(json.dumps([compress(Path(arg)) for arg in sys.argv[1:]], indent=2))
