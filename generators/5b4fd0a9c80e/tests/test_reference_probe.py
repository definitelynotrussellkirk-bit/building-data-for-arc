"""Contract tests for the source-bound independent reference probe."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

from reviewer_support import canonical_path, find_root

TASK_ID = "5b4fd0a9c80e"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
if not HOME.is_dir():
    # Portable runtime layout used by the shared checker.
    HOME = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID
CANONICAL = canonical_path(ROOT)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_probe_binds_sources_and_falsifies_declared_shortcuts():
    probe = _load(HOME / "workspace" / "reference_probe.py", "reference_probe_under_test")
    gen = _load(HOME / "generator.py", "generator_for_reference_probe")
    report = probe.run_probe(
        generator_path=HOME / "generator.py",
        canonical_path=CANONICAL,
        lessons_per_band=2,
        seed_start=700,
    )

    assert report["source_binding"]["probe_sha256"] == hashlib.sha256(
        (HOME / "workspace" / "reference_probe.py").read_bytes()
    ).hexdigest()
    assert report["source_binding"]["generator_sha256"]
    assert report["source_binding"]["generator_version"] == gen.VERSION
    assert report["source_binding"]["rule_hash"] == gen.RULE_HASH
    assert report["canonical"]["pair_count"] == 5
    assert report["canonical"]["train_count"] == 4
    assert report["canonical"]["test_count"] == 1
    assert report["canonical"]["invalid_inputs"] == 0
    assert report["canonical"]["oracle_mismatches"] == 0
    assert report["canonical"]["mirror_mismatches"] == 0
    left_align = report["canonical"]["shortcut_fit"]["left_align"]
    assert left_align["train_agreements"] == left_align["train_pairs"] == 4
    assert left_align["all_agreements"] == left_align["all_pairs"] == 5

    for band in ("default", "easy", "medium", "hard"):
        row = report["bands"][band]
        assert row["lessons"] == 2
        assert row["pairs_seen"] == 8
        assert row["unique_inputs"] == 8
        assert row["invalid_inputs"] == 0
        assert row["oracle_mismatches"] == 0
        assert row["mirror_mismatches"] == 0
        assert row["unidentifiable_lessons"] == 0
        assert all(count == 0 for count in row["competitor_survivors"].values())
    assert report["failures"] == []
