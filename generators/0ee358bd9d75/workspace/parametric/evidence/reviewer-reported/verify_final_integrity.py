"""Recheck a retained prototype census against its own files and live sources."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import find_root


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must be a new file")
    root = find_root(__file__)
    manifest = json.loads((args.evidence / "manifest.private.json").read_text())
    report = json.loads((args.evidence / "census.private.json").read_text())
    mismatches = []
    for kind, base, expected_hashes in (
        ("source", root, manifest["source_hashes"]),
        ("evidence", args.evidence, manifest["files"]),
    ):
        for relative, expected in expected_hashes.items():
            path = base / relative
            actual = sha256(path) if path.is_file() else None
            if actual != expected:
                mismatches.append({"kind": kind, "path": relative, "expected": expected, "actual": actual})
    result = {
        "status": "passed" if not mismatches and report["status"] == "passed" else "failed",
        "scope": "prototype", "payload_argv": sys.argv,
        "source_files_checked": len(manifest["source_hashes"]),
        "evidence_files_checked": len(manifest["files"]), "mismatches": mismatches,
        "generator_sha256": manifest["source_hashes"]["generators/0ee358bd9d75/generator.py"],
        "census_sha256": sha256(args.evidence / "census.private.json"),
        "manifest_sha256": sha256(args.evidence / "manifest.private.json"),
        "verifier_sha256": sha256(Path(__file__)), "counts": report["counts"],
        "automatic_selections": report["automatic_selections"],
        "exact_30_by_30_inputs": report["exact_30_by_30_inputs"],
        "inputs_with_side_over_20": report["inputs_with_side_over_20"],
        "nonzero_colors_per_section": report["nonzero_colors_per_section"],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
