"""Losslessly compact completed JSON receipts using the native gzip contract.

Prefer lesson-census --gzip for new runs. This helper preserves existing report
bytes, verifies both hashes with the repository reader, updates the companion,
then removes only the redundant verified raw copy. Failed cases stay in full.
Run through review.py run; pass explicit paths and a new --receipt destination.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from arcpuzzles.receipt_input import read_receipt


def compact(path):
    path = Path(path).resolve(strict=True)
    if path.suffix != ".json" or not path.is_file():
        raise ValueError(f"expected a completed JSON receipt: {path}")
    raw = path.read_bytes()
    report = json.loads(raw)
    if not isinstance(report, dict) or not report.get("schema"):
        raise ValueError("receipt needs a schema")
    packed = path.with_suffix(".json.gz")
    manifest = path.with_suffix(".compression.json")
    if packed.exists() or manifest.exists():
        raise FileExistsError("compressed receipt destination already exists")
    with packed.open("xb") as output:
        with gzip.GzipFile(fileobj=output, filename="", mode="wb", mtime=0) as stream:
            stream.write(raw)
    packed_bytes = packed.read_bytes()
    row = {"path": path.name, "compressed_path": packed.name,
           "raw_size": len(raw), "raw_sha256": hashlib.sha256(raw).hexdigest(),
           "compressed_size": len(packed_bytes),
           "compressed_sha256": hashlib.sha256(packed_bytes).hexdigest()}
    document = {"schema": "arcpuzzles-evidence-gzip-v1", "compression": "gzip",
                "report_schema": report["schema"], "status": report.get("status"),
                "training_admitted": False,
                "restore_argv": ["python3", "-m", "gzip", "-d", packed.name],
                "restore_note": "Restore a copy in a new directory and verify raw_size/raw_sha256.",
                "files": [row]}
    manifest.write_text(json.dumps(document, indent=2) + "\n")
    verified = read_receipt(packed)
    if verified["raw"] != raw:
        raise ValueError("native reader did not reproduce exact original bytes")
    companion = path.with_suffix(".summary.json")
    if companion.is_file():
        summary = json.loads(companion.read_text())
        summary["full_report"].update(storage="gzip", compressed_path=str(packed),
                                      compressed_sha256=row["compressed_sha256"],
                                      compressed_bytes=len(packed_bytes),
                                      compression_manifest=str(manifest))
        companion.write_text(json.dumps(summary, indent=2) + "\n")
    if path.read_bytes() != raw:
        raise ValueError("source receipt changed while being compressed")
    path.unlink()
    return {**row, "manifest": manifest.name, "native_reader_roundtrip": True,
            "raw_duplicate_removed_after_verification": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    dest = Path(args.receipt)
    if dest.exists():
        raise FileExistsError(dest)
    rows = [compact(path) for path in args.paths]
    result = {"schema": "review-receipt-compaction-v1", "status": "passed", "files": rows,
              "raw_bytes": sum(r["raw_size"] for r in rows),
              "compressed_bytes": sum(r["compressed_size"] for r in rows)}
    dest.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "files"}, sort_keys=True))


if __name__ == "__main__":
    main()
