"""Portable contract for the task-local shortcut evidence tool."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

PROBE_PATH = Path(__file__).resolve().parents[1] / "workspace/probe_shortcut.py"


def _load_probe():
    assert PROBE_PATH.is_file(), "shortcut probe is missing"
    spec = importlib.util.spec_from_file_location("shortcut_probe", PROBE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_shortcut_probe_uses_declared_rivals_and_returns_exact_counterexample():
    probe = _load_probe()
    report = probe.build_report(
        seed=20261019,
        sample_index=0,
        difficulty="medium",
        per_band=2,
        run_racket=False,
    )
    assert report["status"] == "passed"
    assert report["canonical_fit"]["preserve_lower_cells"]["fits_all"]
    exact = report["exact_counterexample"]
    assert exact["witnesses"] == ["erased_unmarked_cell"]
    assert exact["intended_output"] != exact["rivals"]["preserve_lower_cells"]
    assert exact["difference_cells"]
    assert report["emission_probe"]["total"] == 6
    assert report["emission_probe"]["witness_hits"] == 6
    assert report["emission_probe"]["rival_disagreements"]["preserve_lower_cells"] == 6


def test_retained_counterexample_matches_live_declared_contract():
    probe = _load_probe()
    retained_path = (
        Path(__file__).resolve().parents[1]
        / "counterexamples/review-f052cb7cb3f5a69a/preserve-lower-cells.json"
    )
    retained = json.loads(retained_path.read_text(encoding="utf-8"))
    report = probe.build_report(
        seed=retained["sampling"]["seed"],
        sample_index=retained["sampling"]["sample_index"],
        difficulty=retained["sampling"]["difficulty"],
        per_band=1,
        run_racket=False,
    )
    exact = report["exact_counterexample"]
    assert retained["generator_sha256"] == report["generator_sha256"]
    assert retained["declared_rule_hash"] == report["rule_hash_declared"]
    assert retained["input"] == exact["input"]
    assert retained["intended_output"] == exact["intended_output"]
    assert retained["rival_output"] == exact["rivals"]["preserve_lower_cells"]
    assert retained["difference_cells"] == exact["difference_cells_by_rival"]["preserve_lower_cells"]
