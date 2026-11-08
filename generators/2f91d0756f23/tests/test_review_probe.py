"""Regression coverage for the retained source-bound curriculum probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path


PROBE_PATH = Path(__file__).resolve().parents[1] / "workspace/review_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("review_probe_under_test", PROBE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_small_probe_covers_every_cyclic_start_and_declared_rival():
    probe = _load_probe()
    report = probe.run_probe(lessons_per_band=4)

    assert report["source"]["task_id"] == "2f91d0756f23"
    assert report["sampler"]["lessons_per_band"] == 4
    assert report["canonical_shortcuts"]["all_fit_every_canonical_pair"] is True
    assert set(report["canonical_shortcuts"]["by_name"]) == {
        "left_prefix_count",
        "first_two_orbits_only",
    }
    for band in ("easy", "medium", "hard"):
        row = report["bands"][band]
        assert row["cyclic_start_counts"] == {"0": 1, "1": 1, "2": 1, "3": 1}
        assert row["lessons_identifiable"] == 4
        assert row["lessons_unidentifiable"] == 0
        assert row["strict_failures"] == 0
        assert row["generated_inputs"] == 20
        assert row["unique_inputs"] == 20
        assert set(row["rival_disagreements"]) == set(probe.gen.SEMANTIC_RIVALS)
