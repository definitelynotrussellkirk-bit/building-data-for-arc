"""Smoke contract for the reusable distribution/shortcut review probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
PROBE = HOME / "workspace" / "review_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("review_probe_d53534afb2ff", PROBE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_checks_declared_rivals_and_all_cyclic_lesson_starts():
    probe = _load_probe()
    report = probe.run_probe(per_band=2, seeds=(101, 202))

    assert report["task_id"] == "d53534afb2ff"
    assert report["canonical_shortcuts"]
    assert all(item["fits_all_pairs"] for item in report["canonical_shortcuts"].values())
    assert report["lesson_policy"]["cyclic_starts_tested"] == [0, 1, 2, 3]
    assert report["lesson_policy"]["unresolved_lessons"] == []
    assert set(report["first_generated_witnesses"]) == set(
        report["lesson_competitors"]
    )
    palette_counts = report["sampling"]["profile_role_palette_signatures"]
    assert set(palette_counts) == set(report["sampling"]["profile_counts"])
    assert all(count >= 2 for count in palette_counts.values())
