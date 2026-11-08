"""Losslessly retain large census JSON outside the packager's raw checks scan.

Pack: python3 checks/retain_census.py pack --root . --source-dir raw-census
Restore: python3 checks/retain_census.py restore --root . --manifest checks/census/manifest.json
Outputs are hash-verified and existing unequal files are never overwritten.
This helper does not rescore, sample, omit failed lessons, or rewrite source JSON.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def within(root, relative):
    part = Path(relative)
    if part.is_absolute() or ".." in part.parts:
        raise ValueError(f"expected a safe relative path: {relative}")
    path = root / part
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"path escapes root: {relative}")
    return path


def write_new(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise FileExistsError(f"refusing to replace unequal file: {path}")
        return
    with path.open("xb") as handle:
        handle.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("pack", "restore"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-dir", default="raw-census")
    parser.add_argument("--destination", default="checks/census")
    parser.add_argument("--manifest", default="checks/census/manifest.json")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action == "pack":
        source = within(root, args.source_dir)
        destination = within(root, args.destination)
        rows, summaries = [], {}
        for path in sorted(source.glob("*.json")):
            if path.is_symlink():
                raise ValueError(f"source must be a regular file: {path}")
            raw = path.read_bytes()
            report = json.loads(raw)
            compressed = gzip.compress(raw, mtime=0)
            if gzip.decompress(compressed) != raw:
                raise ValueError("compression round-trip mismatch")
            target = destination / (path.name + ".gz")
            write_new(target, compressed)
            rows.append({"original_path": path.relative_to(root).as_posix(),
                         "bytes": len(raw), "sha256": digest(raw),
                         "retained_path": target.relative_to(root).as_posix(),
                         "retained_bytes": len(compressed),
                         "retained_sha256": digest(compressed)})
            keys = ("task_id", "generator_sha256", "declared_rule_hash", "status",
                    "production_status", "rotation_status", "rotation_policy",
                    "summary", "per_band", "sampler", "schedule_coverage",
                    "canonical_rival_fit", "rivals", "limits")
            summaries[path.name] = {key: report[key] for key in keys if key in report}
        if not rows:
            raise ValueError("no census JSON files found")
        manifest = {"schema": "lossless-census-retention-v1", "files": rows,
                    "policy": "Complete original bytes; no lesson filtering or result rewriting.",
                    "restore": ["python3", "checks/retain_census.py", "restore",
                                "--root", ".", "--manifest", args.manifest]}
        encode = lambda obj: (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode()
        write_new(within(root, args.manifest), encode(manifest))
        write_new(destination / "summary.json", encode(summaries))
        print(json.dumps({"files": len(rows), "original_bytes": sum(r["bytes"] for r in rows),
                          "retained_bytes": sum(r["retained_bytes"] for r in rows),
                          "all_roundtrips_verified": True}))
    else:
        manifest = json.loads(within(root, args.manifest).read_text())
        if manifest.get("schema") != "lossless-census-retention-v1":
            raise ValueError("unknown retention manifest")
        for row in manifest["files"]:
            compressed = within(root, row["retained_path"]).read_bytes()
            if len(compressed) != row["retained_bytes"] or digest(compressed) != row["retained_sha256"]:
                raise ValueError("compressed size/hash mismatch")
            # Bound expansion by the exact retained size, then check the original hash.
            with gzip.open(within(root, row["retained_path"]), "rb") as handle:
                raw = handle.read(row["bytes"] + 1)
            if len(raw) != row["bytes"] or digest(raw) != row["sha256"]:
                raise ValueError("restored size/hash mismatch")
            write_new(within(root, row["original_path"]), raw)
        print(json.dumps({"restored_or_verified": len(manifest["files"])}))


if __name__ == "__main__":
    main()
