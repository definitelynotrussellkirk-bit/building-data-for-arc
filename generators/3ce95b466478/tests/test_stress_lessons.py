"""Contract tests for the reusable lesson-window census."""
from __future__ import annotations

from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))

from reference_probe import load_generator  # noqa: E402
from stress_lessons import audit_lessons  # noqa: E402


def test_small_census_checks_every_window_and_declared_rival():
    generator = load_generator()
    report = audit_lessons(
        generator,
        generator_path=HOME / "generator.py",
        bands=("easy",),
        lessons_per_band=6,
        demos_per_lesson=3,
        base_seed=180_000,
    )
    band = report["bands"]["easy"]
    assert band["lessons_checked"] == 6
    assert band["identifiable_lessons"] == 6
    assert band["unidentifiable_lessons"] == []
    assert band["start_modulo_counts"] == {"0": 2, "1": 2, "2": 2}
    assert band["rival_disagreement_demos"] >= 6
    assert report["declared_rivals"] == ["second_largest_perimeter"]
    assert report["canonical_shortcut_fit"]["second_largest_perimeter"] == "5/5"
    assert report["failures"] == []
