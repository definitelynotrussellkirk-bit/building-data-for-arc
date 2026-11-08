"""Regression checks for the task-local curriculum probe."""
from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKSPACE))

import curriculum_probe  # noqa: E402


def test_report_proves_complete_identifiable_lessons():
    report = curriculum_probe.build_report(seed=303, windows=3)

    assert report["ok"] is True
    assert report["examples_needed"] == 4
    assert set(report["declared_profiles"]) == {
        "canonical",
        "empty_column_witness",
        "distractors",
        "mixed_witnesses",
    }
    assert set(report["bands"]) == {"easy", "medium", "hard"}

    declared_rivals = set(report["declared_rivals"])
    assert declared_rivals
    for band, summary in report["bands"].items():
        assert summary["windows_checked"] == 3, band
        assert summary["failures"] == [], band
        assert set(summary["rivals_refuted"]) == declared_rivals, band
        assert summary["mixed_feature_counts"]["empty_column_markers"] >= 3
        assert summary["mixed_feature_counts"]["misaligned_header_color_distractors"] >= 3

    # The report is intended as durable check evidence, not just console text.
    json.dumps(report, sort_keys=True)


if __name__ == "__main__":
    test_report_proves_complete_identifiable_lessons()
    print("curriculum probe test: PASS")
