from __future__ import annotations

import importlib.util
from pathlib import Path
from reviewer_support import find_root


ROOT = find_root(__file__)
PROBE = ROOT / "generators" / "a2d296c74658" / "workspace" / "semantic_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("a2d296c74658_semantic_probe", PROBE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_binds_source_and_checks_complete_sequential_lessons():
    probe = _load_probe()
    report = probe.run_probe(lessons_per_band=8)
    assert len(report["generator_sha256"]) == 64
    assert report["generator_sha256"] == report["generator_sha256_after"]
    assert report["canonical_pair_count"] == 4
    assert all(report["canonical_shortcuts_fit"].values())
    assert report["lesson_policy"]["demos_per_lesson"] == 3
    assert report["lesson_policy"]["query_offset"] == 3
    assert set(report["bands"]) == {"easy", "medium", "hard"}
    for band in report["bands"].values():
        assert band["lessons"] == 8
        assert band["lesson_failures"] == []
        assert band["unique_inputs"] == 11
        assert all(count == 8 for count in band["rivals_killed_in_demos"].values())
