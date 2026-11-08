"""The retained semantic probe is executable and independent of generator labels."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "reference_probe_ffa91bb651d1", HOME / "workspace" / "reference_probe.py"
)
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def test_probe_covers_authority_overrides_and_rotated_lessons():
    report = PROBE.run_probe(per_band=24, lesson_starts=12)
    assert report["status"] == "PASS"
    assert report["canonical"] == {
        "pairs": 5,
        "oracle_mismatches": [],
        "shortcut_survivors": [
            "exactly_three_targets",
            "per_color_exact_pair",
            "row_or_column",
        ],
    }
    assert report["override_matrix"]["failures"] == []
    assert report["lesson_windows"]["all_rotations_identifiable"] is True
    assert report["lesson_windows"]["failures"] == []
    for band in ("easy", "medium", "hard"):
        stats = report["bands"][band]
        assert stats["patterns"] == {"canonical": 12, "comprehensive": 12}
        assert stats["self_check_failures"] == []
        assert stats["deterministic_replay_failures"] == []
        assert stats["oracle_identity_count"] == 0
        assert stats["exact_canonical_profile_hits"] > 0
        assert all(count > 0 for count in stats["rival_counterexamples"].values())
