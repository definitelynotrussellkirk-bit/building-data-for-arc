"""Regression for the reusable source-bound shortcut probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path


PROBE = Path(__file__).resolve().parents[1] / "workspace" / "shortcut_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("shortcut_probe_0f801939eff6", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_reproduces_old_shortcut_and_finds_repaired_witnesses() -> None:
    probe = _load_probe()
    report = probe.build_report(samples_per_band=4, include_authority=False)
    assert report["task_id"] == "0f801939eff6"
    assert report["canonical_shortcut_fit"]["color_frequency_aggregate"] == "5/5"
    assert report["handcrafted_counterexample"]["shortcut_refuted"] is True
    assert report["generated_witnesses"]["disconnected_same_color"]["shortcut_refuted"] is True
    assert report["generated_witnesses"]["equal_area_color_tiebreak"]["shortcut_refuted"] is True
    assert report["census"]["generated"] == 12
    assert report["census"]["color_frequency_refuted"] > 0
    assert report["census"]["position_tiebreak_refuted"] > 0


def test_probe_bootstraps_historical_scripts_namespace() -> None:
    probe = _load_probe()
    probe._ensure_scripts_namespace(probe.find_root(__file__))
    from scripts.comment_solutions import parse_racket

    assert callable(parse_racket)
