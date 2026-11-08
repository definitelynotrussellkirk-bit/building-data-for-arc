"""Regression coverage for the reusable lesson-level finite-rival probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_lesson_probe_uses_declared_rivals_and_rejects_them():
    generator = _load(HOME / "generator.py", "lesson_probe_test_generator")
    probe = _load(HOME / "workspace" / "lesson_probe.py", "lesson_probe_test_tool")

    report = probe.audit_lessons(generator, lessons_per_band=2)

    assert report["totals"]["lessons"] == 6
    assert report["totals"]["rows"] == 24
    assert report["totals"]["unique_inputs"] == 24
    assert report["totals"]["self_check_failures"] == 0
    assert report["totals"]["surviving_competitor_lessons"] == 0
    assert set(report["declared"]["lesson_competitors"]) == set(
        generator.LESSON_COMPETITORS
    )
    assert set(report["declared"]["canonical_shortcuts"]) == set(
        generator.CANONICAL_SHORTCUTS
    )
    assert all(
        row["fits_all"]
        for row in report["canonical_shortcut_fit"].values()
    )
