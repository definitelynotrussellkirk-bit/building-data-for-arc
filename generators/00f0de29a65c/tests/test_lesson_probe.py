"""Checks for the retained source-bound lesson census tool."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))

from lesson_probe import audit_lessons, canonical_pairs, independent_output


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("probe_generator_00f0de29a65c", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_independent_oracle_matches_all_canonical_pairs():
    assert all(independent_output(pair["input"]) == pair["output"] for pair in canonical_pairs())


def test_small_census_refutes_every_declared_competitor():
    report = audit_lessons(_load_generator(), lessons_per_band=4)
    assert report["totals"]["lessons"] == 12
    assert report["totals"]["examples"] == 60
    assert report["totals"]["self_check_errors"] == 0
    assert report["totals"]["oracle_mismatches"] == 0
    assert report["totals"]["unidentifiable_lessons"] == 0
    assert report["totals"]["surviving_competitor_lessons"] == 0
    assert set(report["competitor_refutations"]) == set(_load_generator().LESSON_COMPETITORS)
