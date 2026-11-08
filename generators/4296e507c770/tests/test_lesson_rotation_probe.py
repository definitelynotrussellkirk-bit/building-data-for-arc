"""Regression for the retained cyclic lesson-identifiability probe."""
from __future__ import annotations

import os
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))

from lesson_rotation_probe import audit_rotations  # noqa: E402
from reference_probe import load_generator  # noqa: E402


def test_all_query_rotations_refute_every_declared_competitor():
    module = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
    report = audit_rotations(module, per_band=2)

    assert report["status"] == "pass"
    assert report["lesson_width"] == module.EXAMPLES_NEEDED + 1
    assert report["lessons_checked"] == 6
    assert report["rotations_checked"] == 18
    assert report["ambiguities"] == []
    assert report["competitor_errors"] == []
    assert set(report["competitors"]) == set(module.LESSON_COMPETITORS)
    assert all(row["rotations_passed"] == 6 for row in report["by_band"].values())
