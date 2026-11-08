"""Contract test for the retained source-bound semantic probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_enumerates_declared_rivals_and_all_cyclic_starts():
    generator = _load(TASK_DIR / "generator.py", "d38_probe_generator")
    probe = _load(TASK_DIR / "workspace" / "semantic_probe.py", "d38_semantic_probe")
    report = probe.audit(generator, lessons_per_band=6)

    assert report["passed"] is True
    assert report["lessons_per_band"] == 6
    assert report["lesson_policy"]["demo_count"] == generator.EXAMPLES_NEEDED
    assert report["canonical_shortcuts"] == sorted(generator.CANONICAL_SHORTCUTS)
    assert report["lesson_competitors"] == sorted(generator.LESSON_COMPETITORS)
    for band in ("easy", "medium", "hard"):
        stats = report["bands"][band]
        assert stats["lessons"] == 6
        assert stats["cyclic_starts"] == {"0": 2, "1": 2, "2": 2}
        assert stats["lesson_identifiability_failures"] == 0
        assert stats["self_check_failures"] == 0
        assert stats["distinct_inputs"] > 6
        for name in generator.LESSON_COMPETITORS:
            assert stats["competitors"][name]["lessons_refuted"] == 6
