#!/usr/bin/env python3
"""Rebuild retained parametric evidence in a temporary directory and compare bytes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PACKET = Path(__file__).resolve().parents[1]
REPO = PACKET / "repo"
RETAINED = PACKET / "checks" / "parametric" / "duplicate-precedence-v1"
PROTOTYPE = REPO / "generators" / "83ca9df09514" / "workspace" / "parametric" / "prototype.py"


def tree(path: Path) -> dict[str, str]:
    return {
        item.relative_to(path).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest()
        for item in path.rglob("*")
        if item.is_file()
    }


temporary = Path(tempfile.mkdtemp(prefix="83ca9df09514-rebuild-"))
try:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(PROTOTYPE),
            "--out",
            str(temporary / "evidence"),
            "--seeds",
            "0",
            "1",
            "--demo-count",
            "2",
            "--query-count",
            "4",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"evidence rebuild failed with {completed.returncode}: {completed.stderr}"
        )
    retained = tree(RETAINED)
    rebuilt = tree(temporary / "evidence")
    report = {
        "schema": "83ca9df09514-final-evidence-rebuild-v1",
        "status": "byte_identical" if retained == rebuilt else "different",
        "file_count": len(retained),
        "retained_tree_sha256": hashlib.sha256(
            json.dumps(retained, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "rebuilt_tree_sha256": hashlib.sha256(
            json.dumps(rebuilt, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "missing": sorted(set(retained) - set(rebuilt)),
        "extra": sorted(set(rebuilt) - set(retained)),
        "changed": sorted(
            key for key in set(retained) & set(rebuilt) if retained[key] != rebuilt[key]
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if retained != rebuilt:
        raise SystemExit(1)
finally:
    shutil.rmtree(temporary, ignore_errors=True)
