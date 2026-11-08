"""The task-local probe stays executable and semantically independent."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "reference_probe_2038a3a66886", HOME / "workspace" / "reference_probe.py"
)
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def test_probe_covers_contract_and_canonical_authority():
    report = PROBE.run_probe(per_band=25, lesson_starts=15)
    assert report["status"] == "PASS"
    assert report["canonical"]["pairs"] == 5
    assert report["canonical"]["oracle_mismatches"] == []
    assert report["canonical"]["shortcut_survivors"] == [
        "exact_pair_only",
        "outermost_nonzero",
    ]
    assert report["lesson_windows"]["all_identifiable"] is True
    assert report["lesson_windows"]["failures"] == []
    for band in ("easy", "medium", "hard"):
        stats = report["bands"][band]
        assert stats["patterns"] == {
            "canonical": 5,
            "triple": 5,
            "multi_pair": 5,
            "distractor": 5,
            "combined": 5,
        }
        assert stats["self_check_failures"] == []
        assert stats["oracle_identity_count"] == 0
        assert stats["rival_counterexamples"]["exact_pair_only"] > 0
        assert stats["rival_counterexamples"]["outermost_nonzero"] > 0
