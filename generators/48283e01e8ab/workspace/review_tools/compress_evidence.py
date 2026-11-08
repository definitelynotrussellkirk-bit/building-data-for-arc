#!/usr/bin/env python3
"""Compress an existing JSON receipt without changing or deleting its bytes.

Uses only the Python standard library. Creates adjacent, exclusive .json.gz
and .compression.json files in the native arcpuzzles-evidence-gzip-v1 format.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def compress_evidence(path: Path) -> dict:
    source = Path(path).absolute()
    if any(item.is_symlink() for item in (source, *source.parents)):
        raise ValueError(f"Input must not use symlinks: {source}")
    if source.suffix != ".json" or not source.is_file():
        raise ValueError(f"Input must be an existing regular .json file: {source}")
    source = source.resolve(strict=True)
    if any(char in source.name for char in ("\\", ":", "\0")):
        raise ValueError("Input filename must be portable in a review ZIP")
    packed_path = source.with_suffix(".json.gz")
    manifest_path = source.with_suffix(".compression.json")
    for target in (packed_path, manifest_path):
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"Output already exists: {target}")

    raw = source.read_bytes()
    try:
        document = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f"Input is not valid JSON: {source}") from exc
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0) as stream:
        stream.write(raw)
    packed = buffer.getvalue()
    row = {
        "path": source.name,
        "compressed_path": packed_path.name,
        "raw_size": len(raw),
        "raw_sha256": sha256(raw),
        "compressed_size": len(packed),
        "compressed_sha256": sha256(packed),
    }
    manifest = {
        "schema": "arcpuzzles-evidence-gzip-v1",
        "compression": "gzip",
        "created_from_existing_report": True,
        "training_admitted": False,
        "restore_argv": ["python3", "-m", "gzip", "-d", packed_path.name],
        "restore_note": "Restore a copy in a new directory; verify raw_size and raw_sha256 before using the full report.",
        "files": [row],
    }
    if isinstance(document, dict):
        for key in ("schema", "status"):
            if key in document:
                manifest["report_schema" if key == "schema" else key] = document[key]
    manifest_raw = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")

    created = []
    try:
        for target, body in ((packed_path, packed), (manifest_path, manifest_raw)):
            with target.open("xb") as stream:
                created.append(target)
                stream.write(body)
        # Verify the written files, including exact whitespace/encoding, before
        # reporting success. The input is only ever opened for reading.
        if gzip.decompress(packed_path.read_bytes()) != raw:
            raise ValueError("Written gzip did not preserve the original bytes")
        if manifest_path.read_bytes() != manifest_raw:
            raise ValueError("Written compression manifest differs")
        if source.read_bytes() != raw:
            raise ValueError("Input changed during compression")
    except BaseException:
        # Never touch the original or an output that existed before this call.
        for target in reversed(created):
            target.unlink(missing_ok=True)
        raise

    return {
        "status": "compressed_verified",
        "source": str(source),
        "compressed_path": str(packed_path),
        "manifest_path": str(manifest_path),
        "source_preserved": True,
        "roundtrip_verified": True,
        **{key: row[key] for key in ("raw_size", "raw_sha256", "compressed_size", "compressed_sha256")},
        "manifest_sha256": sha256(manifest_raw),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="existing .json file; originals are always preserved")
    args = parser.parse_args(argv)
    try:
        result = compress_evidence(args.input)
    except (OSError, ValueError) as exc:
        print(f"Compression refused: {exc}", file=sys.stderr)
        return 2
    result.update(utility_sha256=sha256(Path(__file__).read_bytes()), command=sys.argv, cwd=str(Path.cwd()))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
