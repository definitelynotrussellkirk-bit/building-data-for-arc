"""Behavioral test for the reusable public-scalar boundary probe."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


HOME = Path(__file__).resolve().parents[1]


def test_scalar_boundary_probe_accepts_the_fixed_public_contract(tmp_path):
    report_path = tmp_path / "nested" / "scalar-boundary.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(HOME / "workspace" / "scalar_boundary_probe.py"),
            "--generator",
            str(HOME / "generator.py"),
            "--out",
            str(report_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(report_path.read_text())
    assert report["passed"] is True
    assert report["counts"] == {
        "accepted_invalid": 0,
        "accepted_valid": 6,
        "rejected_invalid": 14,
        "rejected_valid": 0,
    }
