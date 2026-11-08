from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from reference_probe import load_generator

HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
GEN = load_generator(GENERATOR_PATH)


def _load_probe():
    path = HOME / "workspace/lesson_probe.py"
    assert path.is_file(), "workspace/lesson_probe.py must provide the source-bound audit"
    spec = importlib.util.spec_from_file_location("lesson_probe_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_lesson_probe_uses_episode_sampler_and_refutes_all_declared_competitors():
    probe = _load_probe()
    report = probe.build_report(
        generator_path=GENERATOR_PATH,
        lessons_per_band=3,
        pairs_per_lesson=4,
        base_seed=9000,
    )

    assert report["schema"] == "arc-lesson-identifiability-probe-v1"
    assert report["sampler"]["algorithm"] == "production_episode_prefix"
    assert report["sampler"]["pairs_per_lesson"] == 4
    assert set(report["declared_competitors"]) == set(GEN.LESSON_COMPETITORS)
    assert set(report["canonical_shortcuts"]) == set(GEN.CANONICAL_SHORTCUTS)
    assert all(item["fits_all_canonical_pairs"] for item in report["canonical_shortcuts"].values())

    for band in ("easy", "medium", "hard"):
        stats = report["bands"][band]
        assert stats["lesson_count"] == 3
        assert stats["pair_count"] == 12
        assert stats["rejected_draw_count"] == 0
        assert stats["unique_input_count"] == 12
        assert stats["domain_violations"] == []
        assert set(stats["competitors"]) == set(GEN.LESSON_COMPETITORS)
        for rival in stats["competitors"].values():
            assert rival["lessons_refuted"] == 3
            assert rival["unrefuted_lesson_indices"] == []
            assert rival["pair_disagreements"] >= 3


def test_cross_lesson_repeats_are_reported_but_do_not_fail_production_sampler_policy():
    probe = _load_probe()
    report = probe.build_report(
        generator_path=GENERATOR_PATH,
        lessons_per_band=2,
        pairs_per_lesson=4,
        base_seed=9100,
    )
    # The production worker rejects duplicates only inside one episode. A grid
    # recurring under another episode seed is distribution evidence, not an
    # invalid lesson, so global uniqueness must not control pass/fail.
    report["bands"]["easy"]["unique_input_count"] = (
        report["bands"]["easy"]["pair_count"] - 1
    )
    assert probe.report_passes(report)
