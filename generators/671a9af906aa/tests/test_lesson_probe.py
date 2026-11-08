"""Smoke-test the reusable source-bound lesson census."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
PROBE = HOME / "workspace" / "lesson_probe.py"
GENERATOR = HOME / "generator.py"


def test_small_probe_is_source_bound_and_identifiable(tmp_path):
    out = tmp_path / "probe.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(PROBE),
            "--repo",
            str(REPO),
            "--generator",
            str(GENERATOR),
            "--out",
            str(out),
            "--lessons-per-band",
            "2",
            "--seed-base",
            "6710900",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(out.read_text())
    expected_sha = hashlib.sha256(GENERATOR.read_bytes()).hexdigest()
    assert report["generator_sha256"] == expected_sha
    assert report["sampler"]["lessons_per_band"] == 2
    assert report["totals"]["lessons"] == 6
    assert report["totals"]["identifiable_lessons"] == 6
    assert report["quality_thresholds"]["minimum_unique_input_fraction"] == 0.95
    assert report["totals"]["unique_input_fraction"] >= 0.95
    assert all(count == 0 for count in report["competitor_survivor_lessons"].values())
    assert all(row["canonical_train_fits"] for row in report["canonical_shortcuts"].values())
