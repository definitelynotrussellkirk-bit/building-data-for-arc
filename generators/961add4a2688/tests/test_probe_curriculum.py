"""Regression tests for the standalone curriculum/override probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
PROBE_PATH = HOME / "workspace" / "probe_curriculum.py"
SPEC = importlib.util.spec_from_file_location("probe_961add4a2688", PROBE_PATH)
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def test_probe_oracle_matches_every_canonical_pair():
    pairs = canonical_pairs("961add4a2688", root=find_root(__file__))
    assert len(pairs) == 5
    assert all(PROBE.independent_rule(pair["input"]) == pair["output"] for pair in pairs)


def test_probe_exhausts_declared_controls_and_rotated_windows():
    report = PROBE.run_probe(seed=20261008, starts=4, bands=("easy", "medium", "hard"))
    assert report["status"] == "passed"
    assert report["summary"] == {
        "override_cases": 216,
        "lessons": 12,
        "rotations": 60,
        "rival_rotation_checks": 300,
    }
    assert report["failures"] == []
