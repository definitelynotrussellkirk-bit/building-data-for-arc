from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "shared" / "runtime"))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_lesson_probe_uses_live_declarations_and_all_cyclic_starts():
    probe = _load(HOME / "workspace" / "lesson_probe.py", "f1347_lesson_probe")
    gen = _load(HOME / "generator.py", "f1347_generator_for_probe")

    report = probe.run_census(
        generator_path=HOME / "generator.py",
        canonical_path=REPO_ROOT / "shared/data/canonical/puzzles.jsonl",
        lessons_per_band=3,
        seed_start=700,
    )

    assert report["source_binding"]["generator_sha256"]
    assert report["source_binding"]["rule_hash"] == gen.RULE_HASH
    assert report["sampler"]["cyclic_starts"] == [0, 1, 2, 3]
    assert set(report["declared_rivals"]) == set(gen.LESSON_COMPETITORS)
    assert set(report["canonical_shortcut_fit"]) == set(gen.CANONICAL_SHORTCUTS)
    assert all(
        row["fits_all_canonical_pairs"]
        for row in report["canonical_shortcut_fit"].values()
    )

    for band in ("easy", "medium", "hard"):
        row = report["bands"][band]
        assert row["lessons"] == 12
        assert row["cyclic_starts_seen"] == [0, 1, 2, 3]
        assert all(count == 0 for count in row["survivors_after_demos"].values())
        assert all(
            count == 0
            for count in row["query_disagreement_survivors"].values()
        )
