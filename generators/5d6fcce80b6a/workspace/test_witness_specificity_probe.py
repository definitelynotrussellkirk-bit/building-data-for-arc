"""Regression tests for the reusable witness-specificity probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_probe():
    path = Path(__file__).with_name("witness_specificity_probe.py")
    spec = importlib.util.spec_from_file_location("witness_specificity_probe", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_uses_matched_controls_and_passes() -> None:
    probe = _load_probe()
    report = probe.run_probe()
    assert report["schema"] == "arc-witness-specificity-v1"
    assert report["task_id"] == "5d6fcce80b6a"
    assert report["passed"] is True
    assert {case["claim"] for case in report["cases"]} == {
        "non_singleton_content_is_preserved",
        "rectangular_canvas_is_doubled",
    }
    for case in report["cases"]:
        assert case["declaration_matches"] is True
        assert case["control"]["witness_fires"] is False
        assert case["control"]["rival_matches_authority"] is True
        assert case["positive"]["witness_fires"] is True
        assert case["positive"]["rival_matches_authority"] is False
        assert case["passed"] is True
