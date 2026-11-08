"""Focused tests for the source-bound whole-lesson census."""
from __future__ import annotations

import importlib.util
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parents[1]
PROBE_PATH = TASK_DIR / "workspace" / "lesson_probe.py"


def load_probe():
    spec = importlib.util.spec_from_file_location("lesson_probe_0da360b839c1", PROBE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_small_census_is_source_bound_and_refutes_every_rival():
    probe = load_probe()
    report = probe.run_census(
        generator_path=TASK_DIR / "generator.py",
        canonical_path=TASK_DIR.parents[1] / "shared" / "data" / "canonical" / "puzzles.jsonl",
        lessons_per_band=3,
    )
    assert report["task_id"] == "0da360b839c1"
    assert report["oracle"]["canonical_pairs_matched"] == 3
    assert all(row["fits_all_usable_pairs"] for row in report["canonical_shortcut_fit"].values())
    for band in ("easy", "medium", "hard"):
        row = report["bands"][band]
        assert row["pinned_lessons"] == 3
        assert row["cyclic_lessons"] == 12
        assert all(count == 0 for count in row["pinned_survivors_after_demos"].values())
        assert all(count == 0 for count in row["cyclic_survivors_after_demos"].values())
        assert row["pinned_unidentifiable"] == 0
        assert row["cyclic_unidentifiable"] == 0
