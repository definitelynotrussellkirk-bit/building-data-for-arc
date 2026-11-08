"""Regressions for the task-local source-bound lesson census."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "lesson_probe_167a1374f6c3", HOME / "workspace" / "lesson_probe.py"
)
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def test_probe_is_source_bound_and_checks_declared_competitors():
    report = PROBE.run_probe(lessons_per_band=3, seed_base=9000)
    expected_hash = hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest()
    assert report["generator_sha256"] == expected_hash
    assert report["lessons_per_band"] == 3
    assert report["sampler"]["cyclic_start_modulus"] == 3
    assert set(report["bands"]) == {"easy", "medium", "hard"}
    assert report["canonical_shortcuts"]["deduplicate_codes"]["fits_all_pairs"]
    for band in report["bands"].values():
        assert band["lessons"] == 3
        assert band["identifiable_lessons"] == 3
        assert band["ambiguous_lessons"] == 0
        assert set(band["competitors"]) == set(PROBE.GEN.LESSON_COMPETITORS)
