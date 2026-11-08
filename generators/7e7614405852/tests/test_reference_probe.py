"""Regression tests for the retained source-bound reviewer probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_HOME = Path(__file__).resolve().parents[1]
PROBE_PATH = TASK_HOME / "workspace" / "reference_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("triple_reference_probe", PROBE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_oracle_matches_all_canonical_outputs():
    probe = _load_probe()
    for pair in canonical_pairs("7e7614405852", root=find_root(__file__)):
        assert probe.reference_output(pair["input"]) == pair["output"]


def test_probe_retains_a_counterexample_for_every_declared_rival():
    probe = _load_probe()
    report = probe.audit(per_band=4)
    assert report["failures"] == []
    assert set(report["counterexamples"]) == set(probe.generator.LESSON_COMPETITORS)
    for band_report in report["bands"].values():
        assert band_report["samples"] == 4
        assert band_report["invalid"] == 0
        assert band_report["oracle_mismatches"] == 0
        assert band_report["unique_inputs"] == 4
