"""Read-only evidence inventory with hashes and lossless gzip size estimates.

Usage: python checks/tooling/inventory_evidence.py --work WORK --out NEW.json
Does not modify, remove, compact, or execute any existing evidence.
"""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--gzip-threshold", type=int, default=1024 * 1024)
    args = parser.parse_args()
    work, output = args.work.resolve(), args.out.absolute()
    if output.exists():
        parser.error("--out already exists; choose a new inventory filename")
    files, duplicates = [], defaultdict(list)
    groups = defaultdict(lambda: {"members": 0, "bytes": 0})
    for path in sorted((work / "checks").rglob("*")):
        if path.is_symlink():
            parser.error(f"Symlink evidence: {path}")
        if not path.is_file() or path.absolute() == output:
            continue
        raw = path.read_bytes()
        name = path.relative_to(work).as_posix()
        digest = hashlib.sha256(raw).hexdigest()
        row = {"path": name, "bytes": len(raw), "sha256": digest}
        if len(raw) >= args.gzip_threshold:
            compressed = gzip.compress(raw, compresslevel=9, mtime=0)
            assert gzip.decompress(compressed) == raw
            row["lossless_gzip_bytes"] = len(compressed)
            row["lossless_gzip_sha256"] = hashlib.sha256(compressed).hexdigest()
        if path.suffix == ".json":
            try:
                value = json.loads(raw)
                if isinstance(value, dict):
                    row["report_identity"] = {key: value[key] for key in
                        ("schema", "status", "passed", "generator_sha256", "generator_hash",
                         "task_id", "phase", "production_status", "rotation_status") if key in value}
            except (ValueError, UnicodeError):
                row["json_parse_failed"] = True
        files.append(row)
        if raw:
            duplicates[digest].append(name)
        group = "/".join(name.split("/")[:2])
        groups[group]["members"] += 1
        groups[group]["bytes"] += len(raw)
    total = sum(row["bytes"] for row in files)
    projected = sum(row.get("lossless_gzip_bytes", row["bytes"]) for row in files)
    result = {"schema": "arcpuzzles-reviewer-evidence-inventory-v1",
              "work_directory": str(work), "scope": "checks/ snapshot excluding inventory output",
              "members": len(files), "bytes": total, "expanded_budget_bytes": 25 * 1024 * 1024,
              "lossless_large_file_gzip_projected_bytes": projected,
              "projection_policy": {"gzip_threshold": args.gzip_threshold, "compression_level": 9,
                                    "mtime": 0, "raw_files_replaced_only_in_separate_staging_copy": True},
              "groups": dict(groups), "files": files,
              "byte_identical_nonempty_groups": [names for names in duplicates.values() if len(names) > 1],
              "budget_note": "This excludes solve/docs/patch/intake overhead. --bundle-evidence reduces outer members, not expanded bytes."}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({key: result[key] for key in ("members", "bytes", "lossless_large_file_gzip_projected_bytes")}, indent=2))
    print(output)


if __name__ == "__main__":
    main()
