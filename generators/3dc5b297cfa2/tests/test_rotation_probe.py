"""Focused tests for the task-local rotation curriculum probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
PROBE = HOME / "workspace" / "rotation_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("rotation_probe", PROBE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_enumerates_the_period_and_all_query_rotations():
    report = _load_probe().run_probe(seeds_per_start=1)
    period = len(report["schedule_profiles"])
    assert report["status"] == "PASS"
    assert report["schedule_starts"] == period
    assert report["lessons"] == 3 * period
    assert report["rotations"] == 3 * report["lessons"]
    assert report["ambiguous_rotations"] == 0
    assert report["minimum_black_demos_after_holdout"] >= 1
