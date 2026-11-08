"""Regression test for the reusable generator census probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent


def _load_probe():
    path = HERE / "review_census.py"
    spec = importlib.util.spec_from_file_location("review_census", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_census_reports_every_band_and_no_unidentifiable_sliding_lessons():
    probe = _load_probe()
    report = probe.build_report(draws=8, seed_count=2, base_seed=25000)

    assert report["task_id"] == "1a4459f1a38f"
    assert set(report["bands"]) == {"easy", "medium", "hard"}
    for band_report in report["bands"].values():
        assert band_report["grids"] == 16
        assert band_report["lesson_windows"]["failed"] == 0
        assert all(count > 0 for count in band_report["semantic_witness_hits"].values())
        assert all(count > 0 for count in band_report["rival_disagreements"].values())
