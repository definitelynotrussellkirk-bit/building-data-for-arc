#!/usr/bin/env python3
"""Task-specific verified staging immediately followed by the official builder.

Every excluded file already has an exact retained copy. This wrapper does not
edit assignments, source, solve summaries or attempt reports. Deleted files
reappeared in the original workspace in this session, including during a build;
construct a fresh staging tree rather than rely on in-place removal.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def digest(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Expected regular file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identical_tree(source, retained):
    for path in source.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Unexpected symlink: {path}")
        if path.is_file() and digest(path) != digest(retained / path.relative_to(source)):
            raise ValueError(f"Retained copy differs: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if not (root / "package_return.py").is_file():
        raise ValueError("Run from the original WORK packet layout")
    excluded = set()
    for bundle_name in ("compressed-before", "compressed-large"):
        bundle = root / "checks" / bundle_name
        command = [sys.executable, str(root / "checks/tooling/evidence-compression/evidence_compression.py"),
                   "verify", "--bundle", str(bundle)]
        subprocess.run(command, cwd=root, check=True)
        manifest = json.loads((bundle / "MANIFEST.json").read_text())
        for row in manifest["files"]:
            relative = Path(row["path"])
            if relative.is_absolute() or ".." in relative.parts or relative.parts[0] != "checks":
                raise ValueError("Only manifest-bound checks evidence may be deduplicated")
            original = root / relative
            if original.exists():
                if original.stat().st_size != row["raw_size"] or digest(original) != row["raw_sha256"]:
                    raise ValueError(f"Raw evidence differs from verified bundle: {relative}")
            excluded.add(relative.as_posix())
    # Opaque private records belong outside the return; their exact copies were
    # retained there during recovery. Never print or inspect their contents.
    private = root / "checks/prior-solve-private"
    if private.exists():
        retained = root / ".review/retained-private-earlier-source"
        identical_tree(private, retained)
    excluded.add("checks/prior-solve-private")
    # The successful misnumbered check remains unmodified under checks/.
    summary = json.loads((root / "solve/summary.json").read_text())
    duplicate = root / "solve/attempts/0002"
    if duplicate.exists():
        if summary.get("status") != "finished" or summary.get("attempt_count") != 1:
            raise ValueError("Unexpected solve state; refusing attempt cleanup")
        identical_tree(duplicate, root / "checks/final-solve-numbering-recovery/attempts/0002")
    excluded.add("solve/attempts/0002")
    receipt = {"schema": "review-build-staging-v2", "excluded_duplicate_paths": sorted(excluded),
               "all_excluded_content_retained": True, "private_content_displayed": False,
               "source_and_assignment_modified": False}
    output = Path(args.out)
    if not output.is_absolute():
        output = root / output
    if output.exists():
        raise FileExistsError(output)

    def ignore(directory, names):
        parent = Path(directory).relative_to(root)
        skipped = []
        for name in names:
            relative = (parent / name).as_posix()
            if relative in excluded:
                skipped.append(name)
            elif parent == Path('.') and (name == '.venv-review' or name.startswith('review_response_')):
                skipped.append(name)
            elif parent == Path('.review') and (name == 'racket-runtime' or name.startswith('retained-private')):
                skipped.append(name)
        return skipped

    with tempfile.TemporaryDirectory(prefix="arc-review-return-") as temporary:
        stage = Path(temporary) / "WORK"
        receipt["official_command"] = ["python3", "package_return.py", "--out", str(output)]
        receipt["official_cwd"] = str(stage)
        (root / "checks/build-staging.json").write_text(json.dumps(receipt, indent=2) + "\n")
        shutil.copytree(root, stage, ignore=ignore)
        for relative in excluded:
            if (stage / relative).exists():
                raise ValueError(f"Duplicate unexpectedly entered staging: {relative}")
        return subprocess.run(["python3", "package_return.py", "--out", str(output)], cwd=stage).returncode


if __name__ == "__main__":
    raise SystemExit(main())
