#!/usr/bin/env python3
"""Verify compressed evidence, archive duplicate raw copies, run the issued builder.

This wrapper does not change the packet builder or any budget. It verifies the
recognized gzip manifest, archives only byte-identical raw duplicates outside
checks/, then invokes the unchanged package_return.py in the same interpreter.
Keeping these operations together avoids a child process observing a stale
filesystem view with both raw and compressed copies. It never filters failures.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
import traceback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    work = args.work.resolve()
    out = args.out.resolve()
    receipt = args.receipt.resolve()
    helper = work / "checks/tooling/evidence-compression/evidence_compression.py"
    spec = importlib.util.spec_from_file_location("retained_evidence_compression", helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    bundle = work / "checks/compressed-raw-checks"
    rows = module.verify(bundle)
    archive = work / ".review/packaging-raw-backups"
    present = []
    # Validate every proposed move before performing any mutation.
    for row in rows:
        if not row["path"].startswith("checks/"):
            raise ValueError("Only reviewer checks may be archived")
        source = work / row["path"]
        if source.exists():
            expected = (row["raw_size"], row["raw_sha256"])
            if module.fingerprint(source) != expected:
                raise ValueError(f"Raw file differs from compressed evidence: {source}")
            target = archive / row["path"]
            if target.exists() and module.fingerprint(target) != expected:
                raise ValueError(f"Existing raw archive differs: {target}")
            present.append((source, target, row))
    if out.exists() or receipt.exists():
        raise FileExistsError("Choose fresh output and receipt paths")
    for source, target, row in present:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(source, target)
        if module.fingerprint(target) != (row["raw_size"], row["raw_sha256"]):
            raise ValueError(f"Raw backup verification failed: {target}")
        source.unlink()
    if any((work / row["path"]).exists() for row in rows):
        raise ValueError("A verified raw duplicate is still in checks/")
    shutil.copy2(work / "RESULTS.json", work / "checks/reviewer_results.json")
    record = {
        "schema": "reviewer-compact-package-v1",
        "work": str(work), "output": str(out),
        "archived_raw_duplicates": [row["path"] for _, _, row in present],
        "compressed_manifest": "checks/compressed-raw-checks/MANIFEST.json",
        "compressed_files_verified": len(rows),
        "raw_bytes_preserved": sum(row["raw_size"] for row in rows),
        "builder": "package_return.py",
        "builder_sha256": hashlib.sha256((work / "package_return.py").read_bytes()).hexdigest(),
        "builder_argv": ["package_return.py", "--bundle-evidence", "--out", str(out)],
        "scope": "Unchanged issued builder; unchanged budgets; all failures preserved in verified gzip streams.",
    }
    old_argv = sys.argv[:]
    old_cwd = Path.cwd()
    try:
        os.chdir(work)
        sys.argv = record["builder_argv"]
        runpy.run_path(str(work / "package_return.py"), run_name="__main__")
        record["status"] = "built"
        record["exit_code"] = 0
        record["zip_sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
        record["zip_bytes"] = out.stat().st_size
    except Exception:
        record["status"] = "failed"
        record["exit_code"] = 1
        record["traceback"] = traceback.format_exc()
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    return record["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
