"""Regression tests for the reusable source-bound lesson probe."""
from __future__ import annotations

import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))

from lesson_probe import run_probe  # noqa: E402


def test_probe_checks_all_query_rotations_and_declared_rivals():
    report = run_probe(per_band=6, seed_base=3000)
    assert report["windows"] == 24
    assert report["rotations"] == 96
    assert report["unique_inputs"] > 80
    assert report["failures"] == []
    assert report["canonical"]["oracle_mismatches"] == 0
    assert report["declared_rivals"] == [
        "drop_thin",
        "global_bbox",
        "identity",
        "largest_only",
    ]
    assert all(count > 0 for count in report["rival_disagreements"].values())
