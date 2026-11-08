"""Regression checks for the reusable independent review probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import canonical_pairs, find_root


HOME = Path(__file__).resolve().parents[1]
PROBE_PATH = HOME / "workspace" / "reference_probe.py"
SPEC = importlib.util.spec_from_file_location("reference_probe_under_test", PROBE_PATH)
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def test_probe_matches_all_canonical_outputs_and_profiles():
    pairs = canonical_pairs("7b0cb3b9a618", root=find_root(__file__))
    assert len(pairs) == 6
    for pair in pairs:
        assert PROBE.rule_output(pair["input"]) == pair["output"]
        observation = PROBE.observe(pair["input"])
        assert observation["answer"] == pair["output"][0][0]
        assert observation["profile"] in PROBE.CANONICAL_PROFILES
        assert observation["orientation"] in {"horizontal", "vertical"}


def test_exhaustive_schedule_probe_has_no_declared_rival_ambiguity():
    report = PROBE.probe_cyclic_lessons(seed=190807)
    assert report["starts"] == 12
    assert report["rotations"] == 48
    assert report["ambiguities"] == []
    assert set(report["profiles_seen"]) == set(PROBE.SCHEDULE_PROFILES)
