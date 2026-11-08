"""The retained source-bound probe stays executable for later reviewers."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / "generators" / "fcd1f7b55d3b"
SPEC = importlib.util.spec_from_file_location(
    "reference_probe_fcd1f7b55d3b", HOME / "workspace" / "reference_probe.py"
)
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def test_probe_covers_authority_overrides_profiles_and_rotated_lessons():
    report = PROBE.run_probe(per_band=24, lesson_starts=12)
    assert report["status"] == "PASS"
    assert report["canonical"]["pairs"] == 5
    assert report["canonical"]["oracle_mismatches"] == []
    assert report["canonical"]["shortcut_survivors"] == [
        "all_colors_bbox",
        "backslash_only",
        "copy_then_fill",
        "exactly_two_pairs",
    ]
    assert report["override_matrix"]["failures"] == []
    assert report["lesson_windows"]["failures"] == []
    assert report["lesson_windows"]["all_rotations_identifiable"] is True
    for band in ("easy", "medium", "hard"):
        stats = report["bands"][band]
        assert stats["self_check_failures"] == []
        assert stats["deterministic_replay_failures"] == []
        assert stats["exact_canonical_profile_hits"] > 0
        assert stats["profiles"]["canonical_backslash"] > 0
        assert stats["profiles"]["canonical_slash"] > 0
        assert stats["profiles"]["selective_backslash"] > 0
        assert stats["profiles"]["selective_slash"] > 0
        assert all(count > 0 for count in stats["rival_counterexamples"].values())
