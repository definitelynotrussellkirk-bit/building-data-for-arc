"""Contract test for the source-bound whole-lesson census."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_lesson_probe_binds_sources_and_falsifies_all_declared_rivals():
    probe = _load(HOME / "workspace" / "lesson_probe.py", "lesson_probe_under_test")
    gen = _load(HOME / "generator.py", "generator_for_probe_test")
    report = probe.run_census(
        generator_path=HOME / "generator.py",
        canonical_path=REPO_ROOT / "shared/data/canonical/puzzles.jsonl",
        lessons_per_band=3,
        seed_start=700,
    )

    assert report["source_binding"]["generator_sha256"]
    assert report["source_binding"]["rule_hash"] == gen.RULE_HASH
    assert report["sampler"]["production_sample_index_start"] == 0
    assert report["sampler"]["demo_count"] == gen.EXAMPLES_NEEDED
    assert report["sampler"]["cyclic_starts"] == list(range(len(gen.SCHEDULE_PROFILES)))
    assert set(report["canonical_shortcut_fit"]) == set(gen.CANONICAL_SHORTCUTS)
    assert all(row["fits_all_usable_pairs"] for row in report["canonical_shortcut_fit"].values())

    for band in ("easy", "medium", "hard"):
        row = report["bands"][band]
        assert row["production_lessons"] == 3
        assert row["production_pairs_seen"] == 15
        assert row["production_unique_inputs"] == 15
        assert row["production_rejections"] == 0
        assert row["cyclic_lessons"] == 12
        assert row["cyclic_starts_seen"] == [0, 1, 2, 3]
        assert all(count == 0 for count in row["production_survivors_after_demos"].values())
        assert all(count == 0 for count in row["cyclic_survivors_after_demos"].values())
        assert all(count > 0 for count in row["production_demo_disagreements"].values())
