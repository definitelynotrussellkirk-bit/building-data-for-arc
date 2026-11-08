"""Regressions for the reusable source-bound lesson/audit probe."""
from __future__ import annotations

import os
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))

from reference_probe import cyclic_lesson_audit, load_generator  # noqa: E402


gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_all_cyclic_schedule_starts_refute_actual_declared_competitors():
    report = cyclic_lesson_audit(gen, cycles_per_band=3)
    assert report["competitors"] == sorted(gen.LESSON_COMPETITORS)
    assert report["canonical_shortcuts"] == ["bbox_width"]
    assert report["canonical_shortcut_fits_all_pairs"] == {"bbox_width": True}
    assert report["lessons"] == 4 * 3 * len(gen.SCHEDULE_PROFILES)
    assert report["hook_failures"] == []
    assert report["surviving_rival_failures"] == []
    assert report["unique_inputs"] >= 4 * 3 * len(gen.SCHEDULE_PROFILES)
